from odoo import models, api
from datetime import datetime, timedelta
from calendar import monthrange


class PosDashboard(models.Model):
    _name = "pos.sales.dashboard"
    _description = "POS Dashboard"

    @api.model
    def get_dashboard_data(self, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):

        today = datetime.today()
        company_id = self.env.company.id

        # -----------------------------
        # DATE FILTER
        # -----------------------------
        if filter_type == "today":
            date_from = today.date()
            date_to = today.date()
        elif filter_type == "week":
            date_from = (today - timedelta(days=7)).date()
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

        # -----------------------------
        # ORDER DOMAIN (DATE + STORE)
        # -----------------------------
        domain = [
            ('date_order', '>=', datetime.combine(date_from, datetime.min.time())),
            ('date_order', '<=', datetime.combine(date_to, datetime.max.time())),
            ('company_id', '=', company_id)
        ]

        if config_id:
            domain.append(('config_id', '=', config_id))

        orders = self.env['pos.order'].search(domain)

        total_sales = sum(orders.mapped("amount_total"))
        total_order_count = len(orders)

        lang = self.env.lang or 'en_US'

        # ---------------------------------------------------------
        # TOP PRODUCTS
        # ---------------------------------------------------------
        product_query = """
            SELECT pol.product_id,
                   SUM(pol.qty),
                   SUM(pol.qty * pol.price_unit)
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            WHERE po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            product_query += " AND po.config_id = %s"
            params.append(config_id)

        product_query += """
            GROUP BY pol.product_id
            ORDER BY SUM(pol.qty) DESC
            LIMIT 10
        """

        self.env.cr.execute(product_query, tuple(params))
        product_rows = self.env.cr.fetchall()

        product_ids = [r[0] for r in product_rows]
        products = []

        if product_ids:
            product_records = self.env['product.product'].browse(product_ids)
            qty_map = {r[0]: r[1] for r in product_rows}
            amount_map = {r[0]: r[2] for r in product_rows}

            for product in product_records:
                products.append(
                    (
                        product.display_name,
                        qty_map.get(product.id, 0),
                        product.id,
                        amount_map.get(product.id, 0)
                    )
                )

        # ---------------------------------------------------------
        # STORE PERFORMANCE
        # ---------------------------------------------------------
        store_query = """
            SELECT pc.name,
                   COUNT(po.id),
                   SUM(po.amount_total)
            FROM pos_order po
            JOIN pos_config pc ON po.config_id = pc.id
            WHERE po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            store_query += " AND po.config_id = %s"
            params.append(config_id)

        store_query += """
            GROUP BY pc.name
            ORDER BY SUM(po.amount_total) DESC
        """

        self.env.cr.execute(store_query, tuple(params))
        stores = self.env.cr.fetchall()

        # STORE RANKING
        store_ranking = []
        rank = 1

        for store in stores:
            store_ranking.append({
                "rank": rank,
                "store": store[0],
                "orders": store[1],
                "sales": store[2] or 0,
            })
            rank += 1

        # ---------------------------------------------------------
        # PAYMENT METHODS
        # ---------------------------------------------------------
        payment_query = f"""
            SELECT ppm.name->>'{lang}' AS name,
                   SUM(pp.amount) AS total
            FROM pos_payment pp
            JOIN pos_payment_method ppm ON pp.payment_method_id = ppm.id
            JOIN pos_order po ON pp.pos_order_id = po.id
            WHERE po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            payment_query += " AND po.config_id = %s"
            params.append(config_id)

        payment_query += f"""
            GROUP BY ppm.name->>'{lang}'
            ORDER BY total DESC
        """

        self.env.cr.execute(payment_query, tuple(params))
        payments = self.env.cr.fetchall()

        # ---------------------------------------------------------
        # TOP CUSTOMERS
        # ---------------------------------------------------------
        customer_query = """
            SELECT rp.id,
                   rp.name,
                   SUM(po.amount_total) AS total
            FROM pos_order po
            JOIN res_partner rp ON po.partner_id = rp.id
            WHERE po.partner_id IS NOT NULL
            AND po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            customer_query += " AND po.config_id = %s"
            params.append(config_id)

        customer_query += """
            GROUP BY rp.id, rp.name
            ORDER BY total DESC
            LIMIT 10
        """

        self.env.cr.execute(customer_query, tuple(params))
        customers = self.env.cr.fetchall()

        # ---------------------------------------------------------
        # USER INFO
        # ---------------------------------------------------------
        user = self.env.user
        user_data = {
            "name": user.name,
            "image": f"/web/image/res.users/{user.id}/image_128"
        }

        # ---------------------------------------------------------
        # POS STATUS COUNTS
        # ---------------------------------------------------------
        open_session_domain = [('state', '=', 'opened'), ('company_id', '=', company_id)]
        closed_session_domain = [('state', '=', 'closed'), ('company_id', '=', company_id)]

        if config_id:
            open_session_domain.append(('config_id', '=', config_id))
            closed_session_domain.append(('config_id', '=', config_id))

        open_sessions = self.env['pos.session'].search_count(open_session_domain)
        closed_sessions = self.env['pos.session'].search_count(closed_session_domain)

        # ---------------------------------------------------------
        # ACTIVE POS SESSIONS
        # ---------------------------------------------------------
        session_domain = [('state', '=', 'opened'), ('company_id', '=', company_id)]
        if config_id:
            session_domain.append(('config_id', '=', config_id))

        sessions = self.env['pos.session'].search(session_domain)

        session_data = [{
            "id": s.id,
            "name": s.config_id.name,
            "session": s.name,
            "user": s.user_id.name,
            "config": s.config_id.name,
            "start_at": s.start_at,
        } for s in sessions]

        # currency
        currency = self.env.company.currency_id
        currency_data = {
            "symbol": currency.symbol,
            "position": currency.position,
        }

        # ---------------------------------------------------------
        # ALL CONFIGS (STORES)
        # ---------------------------------------------------------
        all_configs = self.env['pos.config'].search([('company_id', '=', company_id)])
        all_config_data = [{
            "id": c.id,
            "name": c.name,
        } for c in all_configs]

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
                   SUM(pol.qty) AS qty_sold
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            JOIN product_product pp ON pol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            JOIN {relation_table} rel ON rel.{col1} = pt.id
            JOIN pos_category pc ON pc.id = rel.{col2}
            WHERE po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            category_query += " AND po.config_id = %s"
            params.append(config_id)

        category_query += """
            GROUP BY pc.id, pc.name
            ORDER BY SUM(pol.qty) DESC
            LIMIT 10
        """

        self.env.cr.execute(category_query, tuple(params))
        rows = self.env.cr.fetchall()

        categories = []
        for r in rows:
            name = r[1]
            if isinstance(name, dict):
                name = name.get(self.env.lang, list(name.values())[0])
            categories.append({
                "id": r[0],
                "name": name,
                "qty": r[2],
            })

        # ---------------------------------------------------------
        # TOP CASHIERS (Employee)
        # ---------------------------------------------------------
        top_cashiers = []
        cashier_query = """
            SELECT 
                he.id,
                he.name,
                COUNT(po.id) AS orders,
                COALESCE(SUM(po.amount_total), 0) AS sales
            FROM pos_order po
            JOIN hr_employee he ON po.employee_id = he.id
            WHERE po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            cashier_query += " AND po.config_id = %s"
            params.append(config_id)

        cashier_query += """
            GROUP BY he.id, he.name
            ORDER BY sales DESC
            LIMIT 10
        """

        self.env.cr.execute(cashier_query, tuple(params))
        cashier_rows = self.env.cr.fetchall()
        rank = 1
        for row in cashier_rows:
            top_cashiers.append({
                "rank": rank,
                "id": row[0],
                "name": row[1],
                "orders": row[2],
                "sales": float(row[3] or 0),
            })
            rank += 1

        # ---------------------------------------------------------
        # STORE SALES COMPARISON
        # ---------------------------------------------------------
        period_days = (date_to - date_from).days + 1

        current_start = date_from
        current_end = date_to

        previous_start = current_start - timedelta(days=period_days)
        previous_end = current_end - timedelta(days=period_days)

        current_start_dt = datetime.combine(current_start, datetime.min.time())
        current_end_dt = datetime.combine(current_end, datetime.max.time())
        previous_start_dt = datetime.combine(previous_start, datetime.min.time())
        previous_end_dt = datetime.combine(previous_end, datetime.max.time())
        
        current_session_filter = ""
        previous_session_filter = ""
        if config_id:
            current_session_filter = "AND po.config_id = %s"
            previous_session_filter = "AND po.config_id = %s"

        comparison_query = """
            SELECT pc.name,

                SUM(CASE 
                    WHEN po.date_order >= %s 
                    AND po.date_order <= %s
                    {current_session_filter}
                    THEN po.amount_total ELSE 0
                END) AS current_sales,

                SUM(CASE 
                    WHEN po.date_order >= %s 
                    AND po.date_order <= %s
                    {previous_session_filter}
                    THEN po.amount_total ELSE 0
                END) AS previous_sales

            FROM pos_order po
            JOIN pos_config pc ON po.config_id = pc.id
            WHERE po.company_id = %s
        """

        comparison_query = comparison_query.format(
            current_session_filter=current_session_filter,
            previous_session_filter=previous_session_filter
        )

        params = [
            current_start_dt,
            current_end_dt,
        ]

        if config_id:
            params.append(config_id)

        params += [
            previous_start_dt,
            previous_end_dt,
        ]

        if config_id:
            params.append(config_id)

        params.append(company_id)
        comparison_query += """
            GROUP BY pc.name
            ORDER BY pc.name
        """

        self.env.cr.execute(comparison_query, tuple(params))
        rows = self.env.cr.fetchall()
        store_comparison = []
        for r in rows:
            store_comparison.append({
                "store": r[0],
                "current": r[1] or 0,
                "previous": r[2] or 0,
            })

        # ---------------------------------------------------------
        # NOTIFICATIONS
        # ---------------------------------------------------------
        today_date = datetime.today().date()
        param_key = f"pos_dashboard_last_seen_{user.id}"
        last_seen_id = int(self.env['ir.config_parameter'].sudo().get_param(param_key, 0))

        notification_query = """
            SELECT id, name, amount_total
            FROM pos_order
            WHERE DATE(date_order) = %s
            AND id > %s
            AND company_id = %s
        """

        params = [today_date, last_seen_id, company_id]

        if config_id:
            notification_query += " AND config_id = %s"
            params.append(config_id)

        notification_query += """
            ORDER BY id DESC
            LIMIT 10
        """

        self.env.cr.execute(notification_query, tuple(params))
        notification_orders = self.env.cr.fetchall()
        notification_count = len(notification_orders)
        
        return {
            "total_sales": round(total_sales, 2),
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
            "notification_count": notification_count,
            "currency": currency_data,
            "open_sessions": open_sessions,
            "closed_sessions": closed_sessions,
            "store_comparison": store_comparison,
            "top_cashiers": top_cashiers,
        }

    @api.model
    def get_product_sales_details(self, product_id, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):

        today = datetime.today()
        company_id = self.env.company.id

        if filter_type == "today":
            date_from = today.date()
            date_to = today.date()
        elif filter_type == "week":
            date_from = (today - timedelta(days=7)).date()
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

        query = """
            SELECT pol.id,
                   po.name,
                   po.date_order,
                   pol.qty,
                   pol.price_unit,
                   pol.qty * pol.price_unit
            FROM pos_order_line pol
            JOIN pos_order po ON pol.order_id = po.id
            WHERE pol.product_id = %s
            AND po.date_order >= %s
            AND po.date_order <= %s
            AND po.company_id = %s
        """

        params = [product_id, datetime.combine(date_from, datetime.min.time()), datetime.combine(date_to, datetime.max.time()), company_id]

        if config_id:
            query += " AND po.config_id = %s"
            params.append(config_id)

        query += """
            ORDER BY po.date_order DESC
            LIMIT 30
        """

        self.env.cr.execute(query, tuple(params))
        rows = self.env.cr.fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "order": r[1],
                "date": r[2],
                "qty": r[3],
                "price": r[4],
                "total": r[5],
            })

        return result

    @api.model
    def mark_notifications_read(self):
        user = self.env.user
        last_order = self.env['pos.order'].search(
            [('company_id', '=', self.env.company.id)],
            order="id desc",
            limit=1
        )
        param_key = f"pos_dashboard_last_seen_{user.id}"
        self.env['ir.config_parameter'].sudo().set_param(
            param_key,
            last_order.id if last_order else 0
        )
        return True

    @api.model
    def get_category_products(self, category_id, filter_type="today", config_id=False, custom_date_from=False, custom_date_to=False):

        today = datetime.today()
        company_id = self.env.company.id

        if filter_type == "today":
            date_from = today.date()
            date_to = today.date()
        elif filter_type == "week":
            date_from = (today - timedelta(days=7)).date()
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

        domain = [
            ('order_id.date_order', '>=', datetime.combine(date_from, datetime.min.time())),
            ('order_id.date_order', '<=', datetime.combine(date_to, datetime.max.time())),
            ('order_id.company_id', '=', company_id),
            ('product_id.product_tmpl_id.pos_categ_ids', 'in', [category_id]),
        ]

        if config_id:
            domain.append(('order_id.config_id', '=', config_id))

        lines = self.env['pos.order.line'].search(domain)

        products = {}
        for line in lines:
            product = line.product_id
            qty = line.qty

            if product.id not in products:
                products[product.id] = {
                    "id": product.id,
                    "name": product.display_name,
                    "qty": 0
                }
            products[product.id]["qty"] += qty

        result = sorted(products.values(), key=lambda x: x["qty"], reverse=True)[:30]
        return result
