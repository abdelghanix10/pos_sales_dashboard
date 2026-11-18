from datetime import datetime, timedelta
from odoo import models, api


class PosDashboard(models.Model):
    _name = "pos.sales.dashboard"
    _description = "POS Sales Dashboard"

    def _get_date_range(self, filter_type="today", custom_date_from=False, custom_date_to=False):
        today = datetime.today()
        if filter_type == "today":
            date_from = today.date()
            date_to = today.date()
        elif filter_type == "yesterday":
            yesterday = (today - timedelta(days=1)).date()
            date_from = yesterday
            date_to = yesterday
        elif filter_type == "week":
            date_from = (today - timedelta(days=6)).date()
            date_to = today.date()
        elif filter_type == "month":
            date_from = today.replace(day=1).date()
            date_to = today.date()
        elif filter_type == "year":
            date_from = today.replace(month=1, day=1).date()
            date_to = today.date()
        elif filter_type == "custom":
            date_from = datetime.strptime(custom_date_from, "%Y-%m-%d").date() if custom_date_from else today.date()
            date_to = datetime.strptime(custom_date_to, "%Y-%m-%d").date() if custom_date_to else today.date()
        else:
            date_from = today.date()
            date_to = today.date()
        return date_from, date_to

    @api.model
    def get_dashboard_data(self, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):
        company_id = self.env.company.id
        lang = self.env.lang or 'en_US'
        date_from, date_to = self._get_date_range(filter_type, custom_date_from, custom_date_to)

        dt_from = datetime.combine(date_from, datetime.min.time())
        dt_to = datetime.combine(date_to, datetime.max.time())

        # -----------------------------
        # ORDER DOMAIN (DATE + STORE)
        # -----------------------------
        domain = [
            ('date_order', '>=', dt_from),
            ('date_order', '<=', dt_to),
            ('company_id', '=', company_id),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        if config_id:
            domain.append(('config_id', '=', int(config_id)))

        orders = self.env['pos.order'].search(domain)
        total_sales = sum(orders.mapped("amount_total"))
        total_order_count = len(orders)
        avg_order_value = round(total_sales / total_order_count, 2) if total_order_count else 0.0

        # Previous Period Sales for Growth %
        period_days = max(1, (date_to - date_from).days + 1)
        prev_start_dt = datetime.combine(date_from - timedelta(days=period_days), datetime.min.time())
        prev_end_dt = datetime.combine(date_to - timedelta(days=period_days), datetime.max.time())
        prev_domain = [
            ('date_order', '>=', prev_start_dt),
            ('date_order', '<=', prev_end_dt),
            ('company_id', '=', company_id),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        if config_id:
            prev_domain.append(('config_id', '=', int(config_id)))
        prev_orders = self.env['pos.order'].search(prev_domain)
        prev_total_sales = sum(prev_orders.mapped("amount_total"))
        if prev_total_sales > 0:
            sales_growth = round(((total_sales - prev_total_sales) / prev_total_sales) * 100.0, 1)
        else:
            sales_growth = 100.0 if total_sales > 0 else 0.0

        # ---------------------------------------------------------
        # TOP PRODUCTS
        # ---------------------------------------------------------
        product_query = """
            SELECT pol.product_id,
                   COALESCE(SUM(pol.qty), 0) AS qty,
                   COALESCE(SUM(pol.price_subtotal_incl), 0) AS amount
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            WHERE po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [dt_from, dt_to, company_id]
        if config_id:
            product_query += " AND po.config_id = %s"
            params.append(int(config_id))

        product_query += """
            GROUP BY pol.product_id
            ORDER BY qty DESC
            LIMIT 10
        """
        self.env.cr.execute(product_query, tuple(params))
        product_rows = self.env.cr.fetchall()

        product_ids = [r[0] for r in product_rows if r[0]]
        products = []
        if product_ids:
            product_records = {
                p.id: p.display_name
                for p in self.env['product.product'].browse(product_ids)
            }
            for prod_id, qty, amount in product_rows:
                if prod_id in product_records:
                    products.append((
                        product_records[prod_id],
                        round(float(qty or 0), 2),
                        prod_id,
                        round(float(amount or 0), 2),
                    ))

        # ---------------------------------------------------------
        # STORE PERFORMANCE
        # ---------------------------------------------------------
        store_query = """
            SELECT pc.name,
                   COUNT(po.id),
                   COALESCE(SUM(po.amount_total), 0)
            FROM pos_order po
            JOIN pos_config pc ON po.config_id = pc.id
            WHERE po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [dt_from, dt_to, company_id]
        if config_id:
            store_query += " AND po.config_id = %s"
            params.append(int(config_id))

        store_query += """
            GROUP BY pc.name
            ORDER BY SUM(po.amount_total) DESC
        """
        self.env.cr.execute(store_query, tuple(params))
        raw_stores = self.env.cr.fetchall()

        stores = []
        store_ranking = []
        for rank, s in enumerate(raw_stores, start=1):
            st_name = s[0].get(lang) or next(iter(s[0].values()), "Store") if isinstance(s[0], dict) else s[0]
            st_orders = s[1]
            st_sales = round(float(s[2] or 0), 2)
            stores.append((st_name, st_orders, st_sales))
            store_ranking.append({
                "rank": rank,
                "store": st_name,
                "orders": st_orders,
                "sales": st_sales,
            })

        # ---------------------------------------------------------
        # PAYMENT METHODS (Safe JSONB handling)
        # ---------------------------------------------------------
        payment_query = """
            SELECT COALESCE(ppm.name->>%s, ppm.name->>'en_US', 'Other') AS name,
                   COALESCE(SUM(pp.amount), 0) AS total
            FROM pos_payment pp
            JOIN pos_payment_method ppm ON pp.payment_method_id = ppm.id
            JOIN pos_order po ON pp.pos_order_id = po.id
            WHERE po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [lang, dt_from, dt_to, company_id]
        if config_id:
            payment_query += " AND po.config_id = %s"
            params.append(int(config_id))

        payment_query += """
            GROUP BY COALESCE(ppm.name->>%s, ppm.name->>'en_US', 'Other')
            ORDER BY total DESC
        """
        params.append(lang)
        self.env.cr.execute(payment_query, tuple(params))
        payments = [
            (r[0] or "Other", round(float(r[1] or 0), 2))
            for r in self.env.cr.fetchall()
        ]

        # ---------------------------------------------------------
        # TOP CUSTOMERS (Includes Walk-in Customer fallback)
        # ---------------------------------------------------------
        customer_query = """
            SELECT COALESCE(rp.id, 0) AS partner_id,
                   COALESCE(rp.name, 'Walk-in Customer') AS partner_name,
                   COALESCE(SUM(po.amount_total), 0) AS total
            FROM pos_order po
            LEFT JOIN res_partner rp ON po.partner_id = rp.id
            WHERE po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [dt_from, dt_to, company_id]
        if config_id:
            customer_query += " AND po.config_id = %s"
            params.append(int(config_id))

        customer_query += """
            GROUP BY COALESCE(rp.id, 0), COALESCE(rp.name, 'Walk-in Customer')
            ORDER BY total DESC
            LIMIT 10
        """
        self.env.cr.execute(customer_query, tuple(params))
        customers = [
            (r[0], r[1], round(float(r[2] or 0), 2))
            for r in self.env.cr.fetchall()
        ]

        # ---------------------------------------------------------
        # USER INFO & SESSIONS
        # ---------------------------------------------------------
        user = self.env.user
        user_data = {
            "name": user.name,
            "image": f"/web/image/res.users/{user.id}/image_128",
        }

        open_session_domain = [('state', '=', 'opened'), ('company_id', '=', company_id)]
        closed_session_domain = [('state', '=', 'closed'), ('company_id', '=', company_id)]
        session_domain = [('company_id', '=', company_id)]
        if config_id:
            open_session_domain.append(('config_id', '=', int(config_id)))
            closed_session_domain.append(('config_id', '=', int(config_id)))
            session_domain.append(('config_id', '=', int(config_id)))

        open_sessions = self.env['pos.session'].search_count(open_session_domain)
        closed_sessions = self.env['pos.session'].search_count(closed_session_domain)

        # Show open sessions first, followed by recent sessions so the card is populated
        sessions = self.env['pos.session'].search(
            session_domain,
            order="state desc, start_at desc, id desc",
            limit=10,
        )
        session_data = [{
            "id": s.id,
            "name": s.name,
            "session": s.name,
            "user": s.user_id.name,
            "config": s.config_id.name,
            "start_at": s.start_at.strftime("%Y-%m-%d %H:%M") if s.start_at else "",
            "state": s.state,
        } for s in sessions]

        currency = self.env.company.currency_id
        currency_data = {
            "symbol": currency.symbol,
            "position": currency.position,
        }

        all_configs = self.env['pos.config'].search([('company_id', '=', company_id)])
        all_config_data = [{"id": c.id, "name": c.name} for c in all_configs]

        # ---------------------------------------------------------
        # TOP POS CATEGORIES
        # ---------------------------------------------------------
        field = self.env['product.template']._fields['pos_categ_ids']
        relation_table = field.relation
        col1 = field.column1
        col2 = field.column2

        category_query = f"""
            SELECT pc.id,
                   pc.name,
                   COALESCE(SUM(pol.qty), 0) AS qty_sold
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            JOIN product_product pp ON pol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN {relation_table} rel ON rel.{col1} = pt.id
            JOIN pos_category pc ON pc.id = rel.{col2}
            WHERE po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [dt_from, dt_to, company_id]
        if config_id:
            category_query += " AND po.config_id = %s"
            params.append(int(config_id))

        category_query += """
            GROUP BY pc.id, pc.name
            ORDER BY qty_sold DESC
            LIMIT 10
        """
        self.env.cr.execute(category_query, tuple(params))
        categories = []
        for r in self.env.cr.fetchall():
            name = r[1]
            if isinstance(name, dict):
                name = name.get(lang) or next(iter(name.values()), "Category")
            categories.append({
                "id": r[0],
                "name": name,
                "qty": round(float(r[2] or 0), 2),
            })

        # ---------------------------------------------------------
        # TOP CASHIERS (Supports both pos_hr employee_id and standard user_id)
        # ---------------------------------------------------------
        top_cashiers = []
        has_employee_id = 'employee_id' in self.env['pos.order']._fields

        if has_employee_id:
            cashier_query = """
                SELECT he.id,
                       he.name,
                       COUNT(po.id) AS orders,
                       COALESCE(SUM(po.amount_total), 0) AS sales,
                       'hr.employee' AS model_name
                FROM pos_order po
                JOIN hr_employee he ON po.employee_id = he.id
                WHERE po.date_order >= %s
                  AND po.date_order <= %s
                  AND po.company_id = %s
                  AND po.state IN ('paid', 'done', 'invoiced')
            """
            params = [dt_from, dt_to, company_id]
            if config_id:
                cashier_query += " AND po.config_id = %s"
                params.append(int(config_id))
            cashier_query += " GROUP BY he.id, he.name ORDER BY sales DESC LIMIT 10"
            self.env.cr.execute(cashier_query, tuple(params))
            cashier_rows = self.env.cr.fetchall()
        else:
            cashier_rows = []

        if not cashier_rows:
            user_query = """
                SELECT ru.id,
                       rp.name,
                       COUNT(po.id) AS orders,
                       COALESCE(SUM(po.amount_total), 0) AS sales,
                       'res.users' AS model_name
                FROM pos_order po
                JOIN res_users ru ON po.user_id = ru.id
                JOIN res_partner rp ON ru.partner_id = rp.id
                WHERE po.date_order >= %s
                  AND po.date_order <= %s
                  AND po.company_id = %s
                  AND po.state IN ('paid', 'done', 'invoiced')
            """
            params = [dt_from, dt_to, company_id]
            if config_id:
                user_query += " AND po.config_id = %s"
                params.append(int(config_id))
            user_query += " GROUP BY ru.id, rp.name ORDER BY sales DESC LIMIT 10"
            self.env.cr.execute(user_query, tuple(params))
            cashier_rows = self.env.cr.fetchall()

        for rank, row in enumerate(cashier_rows, start=1):
            top_cashiers.append({
                "rank": rank,
                "id": row[0],
                "name": row[1],
                "orders": row[2],
                "sales": round(float(row[3] or 0), 2),
                "model": row[4],
            })

        # ---------------------------------------------------------
        # STORE SALES COMPARISON
        # ---------------------------------------------------------
        current_session_filter = "AND po.config_id = %s" if config_id else ""
        previous_session_filter = "AND po.config_id = %s" if config_id else ""

        comparison_query = f"""
            SELECT pc.name,
                COALESCE(SUM(CASE
                    WHEN po.date_order >= %s AND po.date_order <= %s {current_session_filter}
                    THEN po.amount_total ELSE 0
                END), 0) AS current_sales,
                COALESCE(SUM(CASE
                    WHEN po.date_order >= %s AND po.date_order <= %s {previous_session_filter}
                    THEN po.amount_total ELSE 0
                END), 0) AS previous_sales
            FROM pos_order po
            JOIN pos_config pc ON po.config_id = pc.id
            WHERE po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
            GROUP BY pc.name
            ORDER BY pc.name
        """
        params = [dt_from, dt_to]
        if config_id:
            params.append(int(config_id))
        params += [prev_start_dt, prev_end_dt]
        if config_id:
            params.append(int(config_id))
        params.append(company_id)

        self.env.cr.execute(comparison_query, tuple(params))
        store_comparison = []
        for r in self.env.cr.fetchall():
            st_name = r[0].get(lang) or next(iter(r[0].values()), "Store") if isinstance(r[0], dict) else r[0]
            store_comparison.append({
                "store": st_name,
                "current": round(float(r[1] or 0), 2),
                "previous": round(float(r[2] or 0), 2),
            })

        # ---------------------------------------------------------
        # SALES TREND (HOURLY FOR TODAY & YESTERDAY, DAILY OTHERWISE)
        # ---------------------------------------------------------
        if filter_type in ("today", "yesterday"):
            trend_query = """
                SELECT TO_CHAR(po.date_order, 'HH24:00') AS bucket,
                       COALESCE(SUM(po.amount_total), 0) AS total
                FROM pos_order po
                WHERE po.date_order >= %s
                  AND po.date_order <= %s
                  AND po.company_id = %s
                  AND po.state IN ('paid', 'done', 'invoiced')
            """
        else:
            trend_query = """
                SELECT TO_CHAR(po.date_order, 'YYYY-MM-DD') AS bucket,
                       COALESCE(SUM(po.amount_total), 0) AS total
                FROM pos_order po
                WHERE po.date_order >= %s
                  AND po.date_order <= %s
                  AND po.company_id = %s
                  AND po.state IN ('paid', 'done', 'invoiced')
            """
        t_params = [dt_from, dt_to, company_id]
        if config_id:
            trend_query += " AND po.config_id = %s"
            t_params.append(int(config_id))
        trend_query += " GROUP BY bucket ORDER BY bucket ASC"
        self.env.cr.execute(trend_query, tuple(t_params))
        sales_trend = [
            {"label": r[0], "sales": round(float(r[1] or 0), 2)}
            for r in self.env.cr.fetchall()
        ]

        # ---------------------------------------------------------
        # NOTIFICATIONS
        # ---------------------------------------------------------
        today_date = datetime.today().date()
        param_key = f"pos_dashboard_last_seen_{user.id}"
        last_seen_id = self.env['ir.config_parameter'].sudo().get_int(param_key) or 0

        notification_query = """
            SELECT id, name, ROUND(CAST(amount_total AS numeric), 2)
            FROM pos_order
            WHERE DATE(date_order) = %s
              AND id > %s
              AND company_id = %s
              AND state IN ('paid', 'done', 'invoiced')
        """
        params = [today_date, last_seen_id, company_id]
        if config_id:
            notification_query += " AND config_id = %s"
            params.append(int(config_id))
        notification_query += " ORDER BY id DESC LIMIT 10"

        self.env.cr.execute(notification_query, tuple(params))
        notification_orders = self.env.cr.fetchall()

        return {
            "total_sales": round(total_sales, 2),
            "sales_growth": sales_growth,
            "avg_order_value": avg_order_value,
            "products": products,
            "stores": stores,
            "store_ranking": store_ranking,
            "payments": payments,
            "customers": customers,
            "total_order_count": total_order_count,
            "sessions": session_data,
            "all_configs": all_config_data,
            "user": user_data,
            "notifications": notification_orders,
            "categories": categories,
            "notification_count": len(notification_orders),
            "currency": currency_data,
            "open_sessions": open_sessions,
            "closed_sessions": closed_sessions,
            "store_comparison": store_comparison,
            "sales_trend": sales_trend,
            "top_cashiers": top_cashiers,
        }

    @api.model
    def get_product_sales_details(self, product_id, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):
        company_id = self.env.company.id
        date_from, date_to = self._get_date_range(filter_type, custom_date_from, custom_date_to)

        query = """
            SELECT pol.id,
                   po.name,
                   TO_CHAR(po.date_order, 'YYYY-MM-DD HH24:MI'),
                   pol.qty,
                   pol.price_unit,
                   pol.price_subtotal_incl
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            WHERE pol.product_id = %s
              AND po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [
            product_id,
            datetime.combine(date_from, datetime.min.time()),
            datetime.combine(date_to, datetime.max.time()),
            company_id,
        ]
        if config_id:
            query += " AND po.config_id = %s"
            params.append(int(config_id))

        query += " ORDER BY po.date_order DESC LIMIT 30"
        self.env.cr.execute(query, tuple(params))

        return [{
            "id": r[0],
            "order": r[1],
            "date": r[2],
            "qty": round(float(r[3] or 0), 2),
            "price": round(float(r[4] or 0), 2),
            "total": round(float(r[5] or 0), 2),
        } for r in self.env.cr.fetchall()]

    @api.model
    def mark_notifications_read(self):
        user = self.env.user
        last_order = self.env['pos.order'].search(
            [('company_id', '=', self.env.company.id)],
            order="id desc",
            limit=1,
        )
        param_key = f"pos_dashboard_last_seen_{user.id}"
        self.env['ir.config_parameter'].sudo().set_int(
            param_key,
            last_order.id if last_order else 0,
        )
        return True

    @api.model
    def get_category_products(self, category_id, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):
        company_id = self.env.company.id
        date_from, date_to = self._get_date_range(filter_type, custom_date_from, custom_date_to)

        domain = [
            ('order_id.date_order', '>=', datetime.combine(date_from, datetime.min.time())),
            ('order_id.date_order', '<=', datetime.combine(date_to, datetime.max.time())),
            ('order_id.company_id', '=', company_id),
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('product_id.product_tmpl_id.pos_categ_ids', 'in', [category_id]),
        ]
        if config_id:
            domain.append(('order_id.config_id', '=', int(config_id)))

        lines = self.env['pos.order.line'].search(domain)
        products = {}
        for line in lines:
            product = line.product_id
            if product.id not in products:
                products[product.id] = {
                    "id": product.id,
                    "name": product.display_name,
                    "qty": 0.0,
                }
            products[product.id]["qty"] = round(products[product.id]["qty"] + line.qty, 2)

        return sorted(products.values(), key=lambda x: x["qty"], reverse=True)[:30]