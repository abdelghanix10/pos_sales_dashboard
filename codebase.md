# __init__.py

```py
from . import models
```

# __manifest__.py

```py
{
    'name': "POS Sales Dashboard",
    'version': "20.0.4.0.0",
    'sequence': 10,
    'author': "Vishnu Sasikumar",
    'category': 'Sales/Point of Sale',
    'summary': "Advanced POS dashboard with analytics, charts, trends, and insights",
    'description': """
POS Sales Dashboard (Odoo 20)
=============================
Provides a modern POS Sales Dashboard inside the Point of Sale backend:
- Real-time sales analytics, Average Order Value, and Period-over-Period growth %
- Hourly & Daily Sales Trend line chart
- Top Selling Products, Top Customers, Top POS Categories, and Top Cashiers
- Store Performance & Period Comparison charts (Bar, Pie & Line)
- Active POS Sessions & Payment Methods overview
- CSV Export, Notifications for new orders, and Dark/Light mode support
    """,
    'depends': ["point_of_sale"],
    'data': [
        "security/ir.access.csv",
        "views/dashboard_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            "https://cdn.jsdelivr.net/npm/chart.js",
            "pos_sales_dashboard/static/src/js/pos_dashboard.js",
            "pos_sales_dashboard/static/src/xml/pos_dashboard.xml",
            "pos_sales_dashboard/static/src/css/pos_dashboard.css",
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

# .gitignore

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Odoo specific
*.pyc
*.pyo
*.pyd
__pycache__/
*.log
*.pid
*.swp
*.swo
*~

# Odoo filestore
/filestore/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
```

# models\__init__.py

```py
from . import pos_dashboard
```

# models\pos_dashboard.py

```py
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
        # TOP CUSTOMERS
        # ---------------------------------------------------------
        customer_query = """
            SELECT rp.id,
                   rp.name,
                   COALESCE(SUM(po.amount_total), 0) AS total
            FROM pos_order po
            JOIN res_partner rp ON po.partner_id = rp.id
            WHERE po.partner_id IS NOT NULL
              AND po.date_order >= %s
              AND po.date_order <= %s
              AND po.company_id = %s
              AND po.state IN ('paid', 'done', 'invoiced')
        """
        params = [dt_from, dt_to, company_id]
        if config_id:
            customer_query += " AND po.config_id = %s"
            params.append(int(config_id))

        customer_query += """
            GROUP BY rp.id, rp.name
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
        if config_id:
            open_session_domain.append(('config_id', '=', int(config_id)))
            closed_session_domain.append(('config_id', '=', int(config_id)))

        open_sessions = self.env['pos.session'].search_count(open_session_domain)
        closed_sessions = self.env['pos.session'].search_count(closed_session_domain)

        sessions = self.env['pos.session'].search(open_session_domain)
        session_data = [{
            "id": s.id,
            "name": s.config_id.name,
            "session": s.name,
            "user": s.user_id.name,
            "config": s.config_id.name,
            "start_at": s.start_at.strftime("%Y-%m-%d %H:%M") if s.start_at else "",
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
        # SALES TREND (HOURLY FOR TODAY, DAILY OTHERWISE)
        # ---------------------------------------------------------
        if filter_type == "today":
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
        # Odoo 20 uses typed get_int() instead of get_param()
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
        # Odoo 20 uses typed set_int() instead of set_param()
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
```

# README.md

```md
 POS Sales Dashboard (Odoo 20)
=========================================

This module provides a modern and interactive **POS Sales Dashboard**
inside the **Odoo 20** Point of Sale backend interface.

It enables real-time business insights, analytics, sales trend visualization,
and performance tracking to help managers make better operational and sales
decisions directly from Point of Sale.

The dashboard consolidates key metrics such as total sales, period-over-period
growth, average basket size, products, customers, stores, cashiers, and sessions
into a single intuitive interface.

Features
========

* **Real-Time POS Sales Analytics**:
  - Total Sales with **Period-over-Period Growth (%)** comparison
  - Total Orders with **Average Order Value (Basket Size)**
  - Top Product & Active Stores KPI cards
* **Hourly & Daily Sales Trend Chart**:
  - Interactive line chart displaying **Hourly Sales** (when filtering by *Today*) or **Daily Sales** (when filtering by *Last 7 Days*, *This Month*, *This Year*, or *Custom Date Range*)
* **Top Selling Products**:
  - Quantity & revenue insights, live product search, Bar Chart toggle, and per-product order history popup
* **CSV Export & Manual Refresh**:
  - Export Top Selling Products directly to an Excel-compatible UTF-8 CSV file
  - One-click manual refresh and live top-bar clock
* **Top Customers & Top POS Categories**:
  - Customer rankings with hoverable avatar previews
  - Category quantity rankings with drill-down product popups
* **Store Performance & Period Comparison**:
  - Store rankings table, Pie Chart toggle, and Current vs. Previous Period Bar Chart comparison
* **Top Cashiers Analytics**:
  - Supports both ``pos_hr`` employees (``hr.employee``) and standard POS users (``res.users``) automatically
* **Active POS Sessions & Payment Methods**:
  - Real-time overview of open POS sessions and payment method totals
* **Smart Filters**:
  - Filter by Store (POS Config) and by *Today*, *Last 7 Days*, *This Month*, *This Year*, or *Custom From/To Dates*
* **Order Notifications & Dark/Light Mode**:
  - Notification bell for new POS orders with "Mark as read" support
  - Persistent Dark Mode and Light Mode toggle
  - Mobile-responsive layout

Usage
=====

1. Go to **Point of Sale → POS Dashboard**.
2. Select **All Stores** or a specific store from the dropdown.
3. Choose a date filter (*Today*, *Last 7 Days*, *This Month*, *This Year*, or a custom date range).
4. Review insights across:
   - Executive KPI Cards (Total Sales + Growth %, Top Product, Active Stores, Total Orders + Avg Basket)
   - Sales Trend Line Chart (Hourly / Daily)
   - Active POS Sessions
   - Top Selling Products (with Search, Bar Chart & CSV Export)
   - Store Performance & Payment Methods Breakdown
   - Top Customers, Top Categories, and Top Cashiers
5. Click **View** or **View More** on any card to open detailed drill-down popups.

Configuration
=============

* No extra configuration required after installation.
* Accessible to users in the **Point of Sale / Administrator** group (read access also configured for POS Users in ``security/ir.access.csv``).

Technical Notes (Odoo 20)
=========================

* **Version**: ``20.0.4.0.0``
* **OWL 3 Architecture**:
  - Uses OWL 3 ``proxy()`` reactive state and mandatory ``this.`` template bindings.
  - Uses Odoo 20 QWeb ``t-out`` directives.
* **Odoo 20 Material Symbols**:
  - Uses Odoo 20 Material Symbols ligature icons (``<i class="oi" data-icon="..."/>``).
* **Unified Access Control**:
  - Configured with Odoo 20's ``security/ir.access.csv`` schema.
* **Charts**:
  - Powered by Chart.js (Line, Bar, and Pie charts) with automatic cleanup on component unmount.


```

# security\ir.access.csv

```csv
id,name,model_id,group_id/id,operation,domain
access_pos_sales_dashboard_user,pos.sales.dashboard.user,pos.sales.dashboard,point_of_sale.group_pos_user,r,
access_pos_sales_dashboard_manager,pos.sales.dashboard.manager,pos.sales.dashboard,point_of_sale.group_pos_manager,crud,
```

# static\src\css\pos_dashboard.css

```css
/* GLOBAL BUTTON */

.btn {
  transition: all 0.25s ease;
}

/* DASHBOARD BACKGROUND */

.o_pos_dashboard {
  padding: 30px;
  background: linear-gradient(135deg, #f5fff7, #ecfdf1);
  min-height: 100%;
  animation: fadeIn 0.6s ease;
  position: relative;

  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* HEADER */

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.dashboard-title {
  font-weight: 600;
  font-size: 24px;
  letter-spacing: 0.3px;
}

/* FILTER BUTTONS */

.filter-buttons {
  display: flex;
  gap: 10px;
}

.filter-btn {
  border: 1px solid #ddd;
  padding: 8px 18px;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.25s ease;
  font-weight: 500;
}

.filter-btn:hover {
  background: #4e73df;
  color: white;
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
}

.filter-btn.active {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: white;
  border-color: #4e73df;
}

/* KPI GRID & STAGGERED ANIMATION */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

/* KPI CARD */
.kpi-card {
  padding: 24px;
  border-radius: 12px;
  color: white;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
  transition: all 0.35s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

/* Icon Background Decoration for Cards */
.kpi-card::after {
  content: "\f080"; /* Default Chart Icon */
  font-family: "FontAwesome";
  position: absolute;
  right: -10px;
  bottom: -10px;
  font-size: 5rem;
  opacity: 0.12;
  transform: rotate(-15deg);
  transition: all 0.4s ease;
}

.kpi-blue::after {
  content: "\f156";
} /* Rupee */
.kpi-green::after {
  content: "\f466";
} /* Box */
.kpi-yellow::after {
  content: "\f54e";
} /* Store */
.kpi-red::after {
  content: "\f291";
} /* Cart */

.kpi-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.15);
}

.kpi-card:hover::after {
  transform: rotate(0deg) scale(1.1);
  opacity: 0.25;
}

/* SHINE EFFECT */
.kpi-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    120deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: 0.6s;
}

.kpi-card:hover::before {
  left: 100%;
}

.kpi-title {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
  opacity: 0.9;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 8px;
}

/* KPI COLORS */
.kpi-blue {
  background: linear-gradient(135deg, #4e73df, #224abe);
}
.kpi-green {
  background: linear-gradient(135deg, #1cc88a, #13855c);
}
.kpi-yellow {
  background: linear-gradient(135deg, #f6c23e, #dda20a);
}
.kpi-red {
  background: linear-gradient(135deg, #e74a3b, #be2617);
}

/* DATA GRID */

.data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* DATA CARD */

.data-card {
  background: white;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transition: all 0.35s ease;
  cursor: pointer;
  border: 1px solid transparent;
  overflow-x: auto;
}

.data-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 35px rgba(0, 0, 0, 0.15);
  border: 1px solid #1cc88a;
  background: #f7fffb;
}

.data-title {
  font-weight: 600;
  margin-bottom: 15px;
  font-size: 15px;
}

/* TABLE */

.modern-table {
  width: 100%;
  border-collapse: collapse;
}

.modern-table th {
  font-size: 13px;
  color: #777;
  padding-bottom: 10px;
  text-align: left;
}

.modern-table td {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}

.modern-table tr:hover {
  background: #f4fff9;
}

/* BADGES */

.qty-pill {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
}

/* SALES VALUE */

.sales-value {
  color: #1cc88a;
  font-weight: 600;
}

/* PAYMENT */

.payment-summary {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.payment-title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 14px;
}

.payment-methods {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.payment-pill {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f7fafc;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  border: 1px solid #eee;
  gap: 8px;
  transition: 0.25s;
}

.payment-pill:hover {
  background: #e8fff4;
  transform: scale(1.05);
}

/* USER PROFILE */

.dashboard-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  padding: 6px 12px;
  border-radius: 30px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.user-name {
  font-weight: 500;
  font-size: 14px;
}

/* NOTIFICATION */

.notification-icon {
  position: relative;
  font-size: 20px;
  cursor: pointer;
  color: #444;
  display: flex;
  align-items: center;
}

.notification-icon:hover {
  color: #4e73df;
}

/* BADGE */

.notification-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background: #e74a3b;
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 50%;
  font-weight: 600;
}

/* DROPDOWN PANEL */

.notification-dropdown {
  position: absolute;
  top: 45px;
  right: 0;
  width: 280px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  animation: dropdownFade 0.25s ease;
  overflow: hidden;
}

@keyframes dropdownFade {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* DROPDOWN HEADER */

.notification-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #eee;
  background: #f9fafb;
}

/* MARK READ */

.mark-read {
  font-size: 12px;
  color: #4e73df;
  cursor: pointer;
}

.mark-read:hover {
  text-decoration: underline;
}

/* LIST */

.notification-list {
  max-height: 240px;
  overflow-y: auto;
}

/* ITEM */

.notification-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f2f2f2;
  font-size: 13px;
  transition: 0.2s;
}

.notification-item:hover {
  background: #f5fff7;
}

.order-ref {
  font-weight: 500;
  color: #333;
}

.order-amount {
  color: #1cc88a;
  font-weight: 600;
}

.top-user-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.top-user-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.top-user-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.dashboard-datetime {
  font-size: 14px;
  font-weight: 500;
  color: #555;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dashboard-datetime i {
  color: #4e73df;
}

.top-user-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* ================= DARK MODE ================= */

.o_pos_dashboard.dark-mode {
  background: #0f172a;
}

/* TEXT COLORS */

.o_pos_dashboard.dark-mode,
.o_pos_dashboard.dark-mode .dashboard-title,
.o_pos_dashboard.dark-mode .data-title,
.o_pos_dashboard.dark-mode .user-name {
  color: #e5e7eb;
}

/* FILTER BUTTONS */

.o_pos_dashboard.dark-mode .filter-btn {
  background: #1e293b;
  border: 1px solid #334155;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .filter-btn:hover {
  background: #4e73df;
  color: white;
}

.o_pos_dashboard.dark-mode .filter-btn.active {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: white;
}

/* DATA CARDS */

.o_pos_dashboard.dark-mode .data-card {
  background: #1e293b;
  border: 1px solid #334155;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.o_pos_dashboard.dark-mode .data-card:hover {
  background: #0f172a;
  border: 1px solid #1cc88a;
}

/* TABLE */

.o_pos_dashboard.dark-mode .modern-table th {
  color: #94a3b8;
}

.o_pos_dashboard.dark-mode .modern-table td {
  border-bottom: 1px solid #334155;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .modern-table tr:hover {
  background: #0f172a;
}

/* PAYMENT */

.o_pos_dashboard.dark-mode .payment-pill {
  background: #1e293b;
  border: 1px solid #334155;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .payment-pill:hover {
  background: #0f172a;
}

/* USER PROFILE */

.o_pos_dashboard.dark-mode .user-profile {
  background: #1e293b;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

/* NOTIFICATIONS */

.o_pos_dashboard.dark-mode .notification-icon {
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .notification-dropdown {
  background: #1e293b;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.6);
}

.o_pos_dashboard.dark-mode .notification-title {
  background: #0f172a;
  border-bottom: 1px solid #334155;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .notification-item {
  border-bottom: 1px solid #334155;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .notification-item:hover {
  background: #0f172a;
}

.o_pos_dashboard.dark-mode .order-ref {
  color: #e5e7eb;
}

/* DATE TIME */

.o_pos_dashboard.dark-mode .dashboard-datetime {
  color: #cbd5f5;
}

/* SCROLLBAR (optional nice touch) */

.o_pos_dashboard.dark-mode ::-webkit-scrollbar {
  width: 8px;
}

.o_pos_dashboard.dark-mode ::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 6px;
}

/* THEME TOGGLE BUTTON */

.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

/* HOVER EFFECT */

.theme-btn:hover {
  transform: scale(1.1) rotate(15deg);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.25);
}

/* ICON STYLE */

.sun-icon {
  color: #f6c23e;
  font-size: 18px;
  animation: sunRotate 6s linear infinite;
}

.moon-icon {
  color: #4e73df;
  font-size: 18px;
}

/* ================= MOBILE RESPONSIVE ================= */

@media (max-width: 768px) {
  .modern-table {
    font-size: 12px;
  }

  .modern-table td {
    padding: 6px 4px;
  }

  /* DASHBOARD PADDING */

  .o_pos_dashboard {
    padding: 15px;
  }

  /* HEADER STACK */

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .dashboard-title {
    font-size: 20px;
  }

  /* FILTER BUTTONS */

  .filter-buttons {
    flex-wrap: wrap;
    gap: 8px;
  }

  .filter-btn {
    padding: 6px 12px;
    font-size: 13px;
  }

  /* KPI GRID → 2 COLUMNS */

  .kpi-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .kpi-card {
    padding: 16px;
  }

  .kpi-value {
    font-size: 22px;
  }

  /* DATA GRID → 1 COLUMN */

  .data-grid {
    grid-template-columns: 1fr;
  }

  /* TABLE FIX */

  .modern-table th,
  .modern-table td {
    font-size: 13px;
  }

  /* USER BAR */

  .top-user-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  /* ICON + FILTER ROW */

  .top-user-right {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    flex-wrap: wrap;
  }

  /* USER PROFILE */

  .user-profile {
    padding: 4px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .user-avatar {
    width: 28px;
    height: 28px;
  }

  /* SESSION FILTER FIX */

  .session-filter {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 13px;
  }

  /* NOTIFICATION ICON ALIGNMENT */

  .notification-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
  }

  /* NOTIFICATION DROPDOWN FIX (MOBILE) */

  .notification-dropdown {
    position: fixed;
    top: 70px;
    left: 50%;
    transform: translateX(-50%);
    width: 92%;
    max-width: 360px;
    right: auto;
    border-radius: 12px;
    z-index: 10001;
  }

  /* BETTER SCROLL FOR MOBILE */

  .notification-list {
    max-height: 260px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* TOUCH FRIENDLY ITEMS */

  .notification-item {
    padding: 14px 16px;
    font-size: 14px;
  }

  /* THEME BUTTON */

  .theme-btn {
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

/* SESSION VIEW MORE BUTTON */

.session-more {
  margin-top: 12px;
  text-align: right;
}

.more-btn {
  background: linear-gradient(135deg, #4e73df, #224abe);
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: 0.25s ease;
}

.more-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.2);
}

/* SESSION POPUP OVERLAY */

.session-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadePopup 0.25s ease;
}

/* POPUP CONTAINER */

.session-popup {
  background: white;
  border-radius: 14px;
  padding: 20px;
  width: 520px;
  max-height: 70vh;
  overflow: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

/* POPUP HEADER */

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  margin-bottom: 15px;
  font-size: 16px;
}

/* CLOSE BUTTON */

.popup-close {
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  transition: 0.2s;
}

.popup-close:hover {
  color: #333;
}

/* POPUP ANIMATION */

@keyframes fadePopup {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* DARK MODE SESSION POPUP */

.o_pos_dashboard.dark-mode .session-popup {
  background: #1e293b;
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .popup-close {
  color: #cbd5f5;
}

.o_pos_dashboard.dark-mode .popup-close:hover {
  color: #fff;
}

@media (max-width: 768px) {
  .session-popup {
    width: 92%;
    max-height: 75vh;
    padding: 16px;
  }

  .session-more {
    text-align: center;
  }

  .more-btn {
    width: 100%;
  }
}

html,
body {
  height: 100%;
  overflow: auto;
}

/* ODOO ACTION VIEW SCROLL FIX */

.o_action_manager,
.o_content,
.o_web_client .o_action_manager {
  height: 100%;
  overflow-y: auto !important;
}

.payment-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  margin-bottom: 8px;
}

.payment-icon i {
  font-size: 16px;
  color: #16a34a;
}

/* SESSION FILTER */

.session-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
}

.session-icon {
  color: #3b82f6;
  font-size: 14px;
}

.session-dropdown {
  border: none;
  outline: none;
  font-size: 14px;
  font-weight: 500;
  background: transparent;
  cursor: pointer;
  padding: 4px 6px;
}

.session-dropdown option {
  padding: 6px;
}

.session-filter:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transition: all 0.2s ease;
}

.rank-badge {
  font-size: 18px;
}

.view-btn {
  background: #4e73df;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: 0.2s;
}

.view-btn:hover {
  background: #1cc88a;
}

.top-product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-toggle-btn {
  border: none;
  background: #f4f6fb;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s ease;
}

.chart-toggle-btn:hover {
  background: #4e73df;
  color: white;
  transform: scale(1.05);
}

.product-chart-container {
  height: 260px;
  animation: fadeChart 0.3s ease;
}

@keyframes fadeChart {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* PRODUCT CHART CONTAINER */

.product-chart-container {
  width: 100%;
  height: 280px;
  position: relative;
}

/* MOBILE FIX */

@media (max-width: 768px) {
  .product-chart-container {
    height: 220px;
  }

  #productChart {
    width: 100% !important;
    height: 100% !important;
  }
}
.activity-feed {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  padding: 8px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 13px;
}

.activity-text {
  font-weight: 500;
}

.activity-time {
  font-size: 11px;
  color: #6b7280;
}

/*top customer images*/
/* Wrapper */
.customer-img-wrapper {
  position: relative;
  display: inline-block;
}

/* Small image */
.customer-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
}

/* Zoom image */
.customer-zoom {
  position: absolute;
  top: -10px;
  left: 40px;

  width: 120px;
  height: 120px;

  border-radius: 12px;
  object-fit: cover;

  background: #fff;
  padding: 4px;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);

  opacity: 0;
  transform: scale(0.8);
  pointer-events: none;

  transition: all 0.25s ease;
  z-index: 999;
}

/* Hover effect */
.customer-img-wrapper:hover .customer-zoom {
  opacity: 1;
  transform: scale(1);
}

.top-product-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.product-search {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
  width: 180px;
}

/* -----------------------------------
   TOP CASHIERS TABLE ENHANCEMENT
----------------------------------- */

/* Rank Badge (1,2,3 highlight) */
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 600;
  color: white;
  background: #94a3b8;
}

/* Top 3 highlight */
.rank-1 {
  background: linear-gradient(135deg, #f6c23e, #dda20a);
} /* Gold */
.rank-2 {
  background: linear-gradient(135deg, #c0c0c0, #8c8c8c);
} /* Silver */
.rank-3 {
  background: linear-gradient(135deg, #cd7f32, #8b5a2b);
} /* Bronze */

/* Cashier Cell (avatar + name) */
.cashier-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Avatar */
.cashier-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
  transition: 0.25s;
}

.cashier-avatar:hover {
  transform: scale(1.1);
  border-color: #4e73df;
}

/* Name */
.cashier-name {
  font-weight: 500;
  color: #333;
}

/* Orders Count */
.orders-count {
  font-weight: 600;
  color: #4e73df;
}

/* Sales Value (already exists but enhanced) */
.sales-value {
  font-weight: 700;
  color: #1cc88a;
}

/* Row hover enhancement */
.modern-table tr:hover .cashier-name {
  color: #1cc88a;
}

/* -----------------------------------
   PERFORMANCE BAR (Optional Advanced UI)
----------------------------------- */

.performance-bar {
  width: 100%;
  height: 6px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  margin-top: 6px;
}

.performance-fill {
  height: 100%;
  background: linear-gradient(135deg, #1cc88a, #13855c);
  border-radius: 6px;
  transition: width 0.4s ease;
}

/* -----------------------------------
   DARK MODE SUPPORT
----------------------------------- */

.o_pos_dashboard.dark-mode .cashier-name {
  color: #e5e7eb;
}

.o_pos_dashboard.dark-mode .cashier-avatar {
  border: 2px solid #334155;
}

.o_pos_dashboard.dark-mode .orders-count {
  color: #60a5fa;
}

.o_pos_dashboard.dark-mode .performance-bar {
  background: #334155;
}

/* -----------------------------------
   MOBILE OPTIMIZATION
----------------------------------- */

@media (max-width: 768px) {
  .cashier-avatar {
    width: 28px;
    height: 28px;
  }

  .cashier-name {
    font-size: 13px;
  }

  .orders-count,
  .sales-value {
    font-size: 13px;
  }

  .rank-badge {
    width: 24px;
    height: 24px;
    font-size: 11px;
  }
}

```

# static\src\js\pos_dashboard.js

```js
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onWillUnmount, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class PosDashboard extends Component {
  static template = "pos_sales_dashboard.Template";

  setup() {
    this.orm = useService("orm");

    // OWL 3 in Odoo 20 uses proxy() instead of useState()
    this.state = proxy({
      sales: 0,
      sales_growth: 0,
      avg_order_value: 0,
      products: [],
      stores: [],
      payments: [],
      customers: [],
      sessions: [],
      all_configs: [],
      total_order_count: 0,
      filter: "today",
      selected_config: null,
      custom_date_from: "",
      custom_date_to: "",
      notifications: [],
      notification_count: 0,
      showNotifications: false,
      user: {},
      current_datetime: new Date().toLocaleString(),
      dark_mode: localStorage.getItem("pos_dashboard_theme") === "dark",
      showSessionPopup: false,
      showProductPopup: false,
      showStoreRankingPopup: false,
      showProductDetails: false,
      product_details: [],
      store_ranking: [],
      showProductChart: false,
      showStorePopup: false,
      categories: [],
      showCategoryPopup: false,
      category_products: [],
      showCategoryProducts: false,
      currency: {},
      showStoreChart: false,
      open_sessions: 0,
      closed_sessions: 0,
      store_comparison: [],
      sales_trend: [],
      showCustomerPopup: false,
      filtered_products: [],
      top_cashiers: [],
      showCashierPopup: false,
    });

    this._clockInterval = setInterval(() => {
      this.state.current_datetime = new Date().toLocaleString();
    }, 1000);

    onWillStart(async () => {
      await this.loadDashboard();
    });

    onWillUnmount(() => {
      clearInterval(this._clockInterval);
      if (this.productChart) this.productChart.destroy();
      if (this.storeChart) this.storeChart.destroy();
      if (this.storeComparisonChart) this.storeComparisonChart.destroy();
      if (this.salesTrendChart) this.salesTrendChart.destroy();
    });
  }

  toggleTheme() {
    this.state.dark_mode = !this.state.dark_mode;
    localStorage.setItem(
      "pos_dashboard_theme",
      this.state.dark_mode ? "dark" : "light",
    );
    setTimeout(() => this._renderAllActiveCharts(), 50);
  }

  toggleStoreChart() {
    this.state.showStoreChart = !this.state.showStoreChart;
    if (this.state.showStoreChart) {
      setTimeout(() => this.renderStoreChart(), 100);
    }
  }

  async loadDashboard() {
    const data = await this.orm.call(
      "pos.sales.dashboard",
      "get_dashboard_data",
      [
        this.state.filter,
        this.state.selected_config,
        this.state.custom_date_from,
        this.state.custom_date_to,
      ],
    );

    this.state.sales = data.total_sales;
    this.state.sales_growth = data.sales_growth || 0;
    this.state.avg_order_value = data.avg_order_value || 0;
    this.state.products = data.products;
    this.state.stores = data.stores;
    this.state.total_order_count = data.total_order_count;
    this.state.payments = data.payments;
    this.state.customers = data.customers;
    this.state.store_ranking = data.store_ranking || [];
    this.state.sessions = data.sessions;
    this.state.all_configs = data.all_configs;
    this.state.user = data.user;
    this.state.notifications = data.notifications || [];
    this.state.notification_count = data.notification_count || 0;
    this.state.categories = data.categories || [];
    this.state.currency = data.currency || {};
    this.state.open_sessions = data.open_sessions || 0;
    this.state.closed_sessions = data.closed_sessions || 0;
    this.state.store_comparison = data.store_comparison || [];
    this.state.sales_trend = data.sales_trend || [];
    this.state.filtered_products = data.products;
    this.state.top_cashiers = data.top_cashiers || [];

    setTimeout(() => this._renderAllActiveCharts(), 50);
  }

  _renderAllActiveCharts() {
    if (this.state.showProductChart) {
      this.renderProductChart();
    }
    if (this.state.showStoreChart) {
      this.renderStoreChart();
    }
    this.renderStoreComparisonChart();
    this.renderSalesTrendChart();
  }

  async changeFilter(ev) {
    const filter = ev.currentTarget.dataset.filter;
    this.state.filter = filter;
    await this.loadDashboard();
  }

  onCustomDateFromChange(ev) {
    this.state.custom_date_from = ev.target.value;
  }

  onCustomDateToChange(ev) {
    this.state.custom_date_to = ev.target.value;
  }

  async changeConfig(ev) {
    const value = ev.target.value;
    this.state.selected_config = value ? parseInt(value, 10) : null;
    await this.loadDashboard();
  }

  toggleNotifications() {
    this.state.showNotifications = !this.state.showNotifications;
  }

  async markNotificationsRead() {
    await this.orm.call("pos.sales.dashboard", "mark_notifications_read", []);
    this.state.notifications = [];
    this.state.notification_count = 0;
    this.state.showNotifications = false;
  }

  openSessionPopup() {
    this.state.showSessionPopup = true;
  }
  closeSessionPopup() {
    this.state.showSessionPopup = false;
  }

  openProductPopup() {
    this.state.showProductPopup = true;
  }
  closeProductPopup() {
    this.state.showProductPopup = false;
  }

  openStoreRankingPopup() {
    this.state.showStoreRankingPopup = true;
  }
  closeStoreRankingPopup() {
    this.state.showStoreRankingPopup = false;
  }

  openCashierPopup() {
    this.state.showCashierPopup = true;
  }
  closeCashierPopup() {
    this.state.showCashierPopup = false;
  }

  async openProductDetails(ev) {
    const productId = parseInt(ev.currentTarget.dataset.product, 10);
    const details = await this.orm.call(
      "pos.sales.dashboard",
      "get_product_sales_details",
      [
        productId,
        this.state.filter,
        this.state.selected_config,
        this.state.custom_date_from,
        this.state.custom_date_to,
      ],
    );
    this.state.product_details = details;
    this.state.showProductDetails = true;
  }

  closeProductDetails() {
    this.state.showProductDetails = false;
  }

  openCustomerPopup() {
    this.state.showCustomerPopup = true;
  }
  closeCustomerPopup() {
    this.state.showCustomerPopup = false;
  }

  toggleProductChart() {
    this.state.showProductChart = !this.state.showProductChart;
    if (this.state.showProductChart) {
      setTimeout(() => this.renderProductChart(), 100);
    }
  }

  onProductSearch(ev) {
    const query = ev.target.value.toLowerCase();
    if (!query) {
      this.state.filtered_products = this.state.products;
      return;
    }
    this.state.filtered_products = this.state.products.filter((p) =>
      p[0].toLowerCase().includes(query),
    );
  }

  async openCategoryProducts(ev) {
    const categoryId = parseInt(ev.currentTarget.dataset.category, 10);
    const products = await this.orm.call(
      "pos.sales.dashboard",
      "get_category_products",
      [
        categoryId,
        this.state.filter,
        this.state.selected_config,
        this.state.custom_date_from,
        this.state.custom_date_to,
      ],
    );
    this.state.category_products = products;
    this.state.showCategoryProducts = true;
  }

  openStorePopup() {
    this.state.showStorePopup = true;
  }
  closeStorePopup() {
    this.state.showStorePopup = false;
  }

  openCategoryPopup() {
    this.state.showCategoryPopup = true;
  }
  closeCategoryPopup() {
    this.state.showCategoryPopup = false;
  }

  closeCategoryProducts() {
    this.state.showCategoryProducts = false;
  }

  exportProductsCSV() {
    const headers = ["Product", "Quantity Sold", "Total Sales"];
    const rows = this.state.products.map((p) => [p[0], p[1], p[3]]);
    const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const csv =
      "\uFEFF" +
      [
        headers.map(escape).join(","),
        ...rows.map((r) => r.map(escape).join(",")),
      ].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pos_top_products_${this.state.filter}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  renderSalesTrendChart() {
    const canvas = document.getElementById("salesTrendChart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    if (this.salesTrendChart) {
      this.salesTrendChart.destroy();
    }
    const labels = this.state.sales_trend.map((t) => t.label);
    const values = this.state.sales_trend.map((t) => t.sales);

    this.salesTrendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Sales",
            data: values,
            borderColor: "#1cc88a",
            backgroundColor: "rgba(28, 200, 138, 0.15)",
            fill: true,
            tension: 0.35,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: this.state.dark_mode ? "#e5e7eb" : "#333" },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: { color: this.state.dark_mode ? "#e5e7eb" : "#333" },
            grid: { color: this.state.dark_mode ? "#334155" : "#e5e7eb" },
          },
        },
      },
    });
  }

  renderProductChart() {
    const canvas = document.getElementById("productChart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    if (this.productChart) {
      this.productChart.destroy();
    }
    const products = this.state.products.slice(0, 5);
    const labels = products.map((p) => p[0]);
    const qtyValues = products.map((p) => p[1]);
    const amountValues = products.map((p) => p[3] || 0);

    this.productChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Qty Sold",
            data: qtyValues,
            backgroundColor: [
              "#4e73df",
              "#1cc88a",
              "#f6c23e",
              "#e74a3b",
              "#36b9cc",
            ],
            borderRadius: 6,
            barPercentage: 0.6,
            categoryPercentage: 0.6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const qty = context.raw;
                const amount = amountValues[context.dataIndex] || 0;
                return [
                  "Qty Sold : " + qty,
                  "Sales : " +
                    (this.state.currency.symbol || "") +
                    amount.toLocaleString(),
                ];
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: this.state.dark_mode ? "#e5e7eb" : "#333",
              autoSkip: false,
              maxRotation: 45,
              minRotation: 30,
              font: { size: 10 },
            },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: this.state.dark_mode ? "#e5e7eb" : "#333",
              font: { size: 10 },
            },
            grid: {
              color: this.state.dark_mode ? "#334155" : "#e5e7eb",
            },
          },
        },
      },
    });
  }

  renderStoreChart() {
    const canvas = document.getElementById("storeChart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    if (this.storeChart) {
      this.storeChart.destroy();
    }
    const stores = this.state.stores.slice(0, 5);
    const labels = stores.map((s) => s[0]);
    const values = stores.map((s) => s[2]);

    this.storeChart = new Chart(ctx, {
      type: "pie",
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: [
              "#4e73df",
              "#1cc88a",
              "#f6c23e",
              "#e74a3b",
              "#36b9cc",
            ],
            borderWidth: 1,
            borderColor: this.state.dark_mode ? "#0f172a" : "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: this.state.dark_mode ? "#e5e7eb" : "#333",
              font: { size: 12 },
            },
          },
          tooltip: {
            callbacks: {
              label: (context) =>
                `${context.label} : ${this.state.currency.symbol || ""}${context.raw.toLocaleString()}`,
            },
          },
        },
      },
    });
  }

  renderStoreComparisonChart() {
    const canvas = document.getElementById("storeComparisonChart");
    if (!canvas || typeof Chart === "undefined") return;
    const ctx = canvas.getContext("2d");
    if (this.storeComparisonChart) {
      this.storeComparisonChart.destroy();
    }
    const data = this.state.store_comparison;
    const labels = data.map((s) => s.store);
    const current = data.map((s) => s.current);
    const previous = data.map((s) => s.previous);

    this.storeComparisonChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Current Period",
            data: current,
            backgroundColor: "#4e73df",
          },
          {
            label: "Previous Period",
            data: previous,
            backgroundColor: "#f59e0b",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }
}

registry.category("actions").add("pos_dashboard", PosDashboard);

```

# static\src\xml\pos_dashboard.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="pos_sales_dashboard.Template">
        <div class="o_pos_dashboard container-fluid" t-attf-class="{{ this.state.dark_mode ? 'dark-mode' : '' }}">

            <!-- ================= TOP USER ROW ================= -->
            <div class="top-user-bar">
                <div class="dashboard-datetime">
                    <i class="oi" data-icon="schedule"/>
                    <span t-out="this.state.current_datetime"/>
                </div>

                <div class="top-user-right">
                    <!-- REFRESH & EXPORT -->
                    <button class="theme-btn" title="Refresh Dashboard" t-on-click="() => this.loadDashboard()">
                        <i class="oi" data-icon="refresh"/>
                    </button>
                    <button class="theme-btn" title="Export Top Products CSV" t-on-click="() => this.exportProductsCSV()">
                        <i class="oi" data-icon="download"/>
                    </button>

                    <!-- NOTIFICATION -->
                    <div class="notification-icon">
                        <i class="oi" data-icon="notifications" t-on-click="() => this.toggleNotifications()"/>
                        <span class="notification-badge" t-if="this.state.notification_count">
                            <t t-out="this.state.notification_count"/>
                        </span>

                        <div class="notification-dropdown" t-if="this.state.showNotifications">
                            <div class="notification-title">
                                Latest Orders
                                <span class="mark-read" t-on-click="() => this.markNotificationsRead()">
                                    Mark as read
                                </span>
                            </div>
                            <div class="notification-list">
                                <t t-foreach="this.state.notifications" t-as="n" t-key="n[0]">
                                    <div class="notification-item">
                                        <span class="order-ref">
                                            <t t-out="n[1]"/>
                                        </span>
                                        <span class="order-amount">
                                            <t t-out="this.state.currency.symbol"/> <t t-out="n[2]"/>
                                        </span>
                                    </div>
                                </t>
                            </div>
                        </div>
                    </div>

                    <!-- DARK MODE TOGGLE -->
                    <div class="theme-toggle">
                        <button class="theme-btn" t-on-click="() => this.toggleTheme()">
                            <t t-if="this.state.dark_mode">
                                <i class="oi sun-icon" data-icon="light_mode"/>
                            </t>
                            <t t-else="">
                                <i class="oi moon-icon" data-icon="dark_mode"/>
                            </t>
                        </button>
                    </div>
                </div>
            </div>

            <!-- ================= SECOND HEADER ================= -->
            <div class="dashboard-header">
                <h2 class="dashboard-title">POS Analytics</h2>

                <div class="session-filter">
                    <i class="oi session-icon" data-icon="store"/>
                    <select class="session-dropdown" t-on-change="(ev) => this.changeConfig(ev)">
                        <option t-att-selected="this.state.selected_config === null" value="">
                            All Stores
                        </option>
                        <t t-foreach="this.state.all_configs" t-as="c" t-key="c.id">
                            <option t-att-value="c.id" t-att-selected="this.state.selected_config === c.id">
                                <t t-out="c.name"/>
                            </option>
                        </t>
                    </select>
                </div>

                <div class="filter-buttons" style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <button t-on-click="(ev) => this.changeFilter(ev)"
                            data-filter="today"
                            t-att-class="'filter-btn ' + (this.state.filter === 'today' ? 'active' : '')">
                        Today
                    </button>
                    <button t-on-click="(ev) => this.changeFilter(ev)"
                            data-filter="week"
                            t-att-class="'filter-btn ' + (this.state.filter === 'week' ? 'active' : '')">
                        Last 7 Days
                    </button>
                    <button t-on-click="(ev) => this.changeFilter(ev)"
                            data-filter="month"
                            t-att-class="'filter-btn ' + (this.state.filter === 'month' ? 'active' : '')">
                        This Month
                    </button>
                    <button t-on-click="(ev) => this.changeFilter(ev)"
                            data-filter="year"
                            t-att-class="'filter-btn ' + (this.state.filter === 'year' ? 'active' : '')">
                        This Year
                    </button>

                    <div class="custom-date-filter" style="display: flex; align-items: center; gap: 5px;">
                        <span>From:</span>
                        <input type="date" class="date-input"
                               t-att-value="this.state.custom_date_from"
                               t-on-change="(ev) => this.onCustomDateFromChange(ev)"
                               style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;"/>
                        <span>To:</span>
                        <input type="date" class="date-input"
                               t-att-value="this.state.custom_date_to"
                               t-on-change="(ev) => this.onCustomDateToChange(ev)"
                               style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;"/>
                        <button t-on-click="(ev) => this.changeFilter(ev)"
                                data-filter="custom"
                                t-att-class="'filter-btn ' + (this.state.filter === 'custom' ? 'active' : '')">
                            Apply
                        </button>
                    </div>
                </div>
            </div>

            <!-- ================= KPI CARDS ================= -->
            <div class="kpi-grid">
                <div class="kpi-card kpi-blue">
                    <div class="kpi-title">Total Sales</div>
                    <div class="kpi-value">
                        <t t-out="this.state.currency.symbol"/> <t t-out="this.state.sales"/>
                    </div>
                    <div class="small mt-1" style="opacity: 0.9;">
                        vs prev period: <strong><t t-out="(this.state.sales_growth &gt;= 0 ? '+' : '') + this.state.sales_growth + '%'"/></strong>
                    </div>
                </div>

                <div class="kpi-card kpi-green">
                    <div class="kpi-title">Top Product</div>
                    <div class="kpi-value">
                        <t t-if="this.state.products.length">
                            <t t-out="this.state.products[0][0]"/>
                        </t>
                        <t t-else="">-</t>
                    </div>
                </div>

                <div class="kpi-card kpi-yellow">
                    <div class="kpi-title">Active Stores</div>
                    <div class="kpi-value">
                        <t t-out="this.state.stores.length"/>
                    </div>
                </div>

                <div class="kpi-card kpi-red">
                    <div class="kpi-title">Total Orders</div>
                    <div class="kpi-value">
                        <t t-out="this.state.total_order_count"/>
                    </div>
                    <div class="small mt-1" style="opacity: 0.9;">
                        Avg Basket: <strong><t t-out="this.state.currency.symbol"/> <t t-out="this.state.avg_order_value"/></strong>
                    </div>
                </div>
            </div>

            <!-- ================= DATA GRID ================= -->
            <div class="data-grid">

                <!-- SALES TREND LINE CHART -->
                <div class="data-card">
                    <div class="data-title">📈 Sales Trend (<t t-out="this.state.filter === 'today' ? 'Hourly' : 'Daily'"/>)</div>
                    <div class="product-chart-container">
                        <canvas id="salesTrendChart"/>
                    </div>
                </div>

                <!-- ACTIVE SESSIONS -->
                <div class="data-card">
                    <div class="data-title">🟢 Active POS Sessions</div>
                    <table class="modern-table">
                        <thead>
                            <tr>
                                <th>Session</th>
                                <th>Cashier</th>
                                <th>Store</th>
                                <th>Opening Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="this.state.sessions.slice(0,5)" t-as="s" t-key="s.id">
                                <tr>
                                    <td><t t-out="s.name"/></td>
                                    <td><t t-out="s.user"/></td>
                                    <td><t t-out="s.config"/></td>
                                    <td><t t-out="s.start_at"/></td>
                                </tr>
                            </t>
                        </tbody>
                    </table>

                    <div class="session-more" t-if="this.state.sessions.length &gt; 5">
                        <button class="more-btn" t-on-click="() => this.openSessionPopup()">
                            View More (<t t-out="this.state.sessions.length - 5"/>)
                        </button>
                    </div>
                </div>

                <!-- STORE SALES COMPARISON -->
                <t t-if="this.state.filter === 'month' or this.state.filter === 'year'">
                    <div class="data-card">
                        <div class="data-title">📊 Store Sales Comparison</div>
                        <div class="product-chart-container">
                            <canvas id="storeComparisonChart"/>
                        </div>
                    </div>
                </t>

                <!-- TOP PRODUCTS -->
                <div class="data-card glass-card">
                    <div class="data-title top-product-header">
                        <span>🔥 Top Selling Products</span>
                        <t t-if="!this.state.showProductChart">
                            <input type="text"
                                   class="product-search"
                                   placeholder="Search product..."
                                   t-on-input="(ev) => this.onProductSearch(ev)"/>
                        </t>
                        <button class="chart-toggle-btn" t-on-click="() => this.toggleProductChart()">
                            <t t-if="this.state.showProductChart">
                                <i class="oi" data-icon="list" title="Show List View"/>
                            </t>
                            <t t-else="">
                                <i class="oi" data-icon="bar_chart" title="Show Bar Chart"/>
                            </t>
                        </button>
                    </div>

                    <t t-if="!this.state.showProductChart">
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                    <th>History</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.filtered_products.slice(0,5)" t-as="p" t-key="p[2]">
                                    <tr>
                                        <td><t t-out="p[0]"/></td>
                                        <td>
                                            <span class="qty-pill">
                                                <t t-out="p[1]"/>
                                            </span>
                                        </td>
                                        <td>
                                            <button class="view-btn"
                                                    t-on-click="(ev) => this.openProductDetails(ev)"
                                                    t-att-data-product="p[2]">
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </t>

                    <t t-if="this.state.showProductChart">
                        <div class="product-chart-container">
                            <canvas id="productChart" title="Bar Chart"/>
                        </div>
                    </t>

                    <t t-if="!this.state.showProductChart">
                        <div class="session-more" t-if="this.state.products.length &gt; 5">
                            <button class="more-btn" t-on-click="() => this.openProductPopup()">
                                View More (<t t-out="this.state.products.length - 5"/>)
                            </button>
                        </div>
                    </t>
                </div>

                <!-- STORE PERFORMANCE -->
                <div class="data-card">
                    <div class="data-title top-product-header">
                        <span>📊 Store Performance</span>
                        <button class="chart-toggle-btn" t-on-click="() => this.toggleStoreChart()">
                            <t t-if="this.state.showStoreChart">
                                <i class="oi" data-icon="list" title="Show List View"/>
                            </t>
                            <t t-else="">
                                <i class="oi" data-icon="pie_chart" title="Show Pie Chart"/>
                            </t>
                        </button>
                    </div>

                    <t t-if="!this.state.showStoreChart">
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Store</th>
                                    <th>Orders</th>
                                    <th>Sales</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-set="rank" t-value="1"/>
                                <t t-foreach="this.state.stores.slice(0,6)" t-as="s" t-key="s[0]">
                                    <tr>
                                        <td><t t-out="rank"/></td>
                                        <td><t t-out="s[0]"/></td>
                                        <td><t t-out="s[1]"/> Orders</td>
                                        <td class="sales-value">
                                            <t t-out="this.state.currency.symbol"/> <t t-out="s[2]"/>
                                        </td>
                                    </tr>
                                    <t t-set="rank" t-value="rank + 1"/>
                                </t>
                            </tbody>
                        </table>
                    </t>

                    <t t-if="this.state.showStoreChart">
                        <div class="product-chart-container">
                            <canvas id="storeChart" title="Pie Chart"/>
                        </div>
                    </t>

                    <t t-if="!this.state.showStoreChart">
                        <div class="session-more" t-if="this.state.stores.length &gt; 3">
                            <button class="more-btn" t-on-click="() => this.openStorePopup()">
                                View More (<t t-out="this.state.stores.length - 3"/>)
                            </button>
                        </div>
                    </t>

                    <div class="payment-summary">
                        <div class="payment-title">Payment Methods</div>
                        <div class="payment-methods">
                            <t t-foreach="this.state.payments" t-as="p" t-key="p[0]">
                                <div class="payment-pill">
                                    <span class="payment-icon">
                                        <i class="oi"
                                           t-att-data-icon="p[0].toLowerCase() === 'cash' ? 'payments' : (p[0].toLowerCase() === 'card' ? 'credit_card' : 'account_balance_wallet')"/>
                                    </span>
                                    <span class="payment-name">
                                        <t t-out="p[0]"/>
                                    </span>
                                    <span class="payment-value">
                                        <t t-out="this.state.currency.symbol"/> <t t-out="p[1]"/>
                                    </span>
                                </div>
                            </t>
                        </div>
                    </div>
                </div>

                <!-- TOP CUSTOMERS -->
                <div class="data-card">
                    <div class="data-title">⭐ Top Customers</div>
                    <table class="modern-table">
                        <thead>
                            <tr>
                                <th>Customer</th>
                                <th>Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="this.state.customers.slice(0,5)" t-as="c" t-key="c[0]">
                                <tr>
                                    <td style="display:flex; align-items:center; gap:10px;">
                                        <div class="customer-img-wrapper">
                                            <img t-att-src="'/web/image/res.partner/' + c[0] + '/image_128'" class="customer-avatar"/>
                                            <img t-att-src="'/web/image/res.partner/' + c[0] + '/image_128'" class="customer-zoom"/>
                                        </div>
                                        <span><t t-out="c[1]"/></span>
                                    </td>
                                    <td class="sales-value">
                                        <t t-out="this.state.currency.symbol"/> <t t-out="c[2]"/>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>

                    <div class="session-more" t-if="this.state.customers.length &gt; 5">
                        <button class="more-btn" t-on-click="() => this.openCustomerPopup()">
                            View More (<t t-out="this.state.customers.length - 5"/>)
                        </button>
                    </div>
                </div>

                <!-- TOP CATEGORIES -->
                <div class="data-card">
                    <div class="top-product-header">
                        <div class="data-title">📦 Top POS Product Categories</div>
                    </div>
                    <table class="modern-table">
                        <thead>
                            <tr>
                                <th>Category</th>
                                <th>Qty</th>
                                <th>History</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="this.state.categories.slice(0,5)" t-as="cat" t-key="cat.id">
                                <tr>
                                    <td><t t-out="cat.name"/></td>
                                    <td>
                                        <span class="qty-pill">
                                            <t t-out="cat.qty"/>
                                        </span>
                                    </td>
                                    <td>
                                        <button class="view-btn"
                                                t-on-click="(ev) => this.openCategoryProducts(ev)"
                                                t-att-data-category="cat.id">
                                            View
                                        </button>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>

                    <div class="session-more" t-if="this.state.categories and this.state.categories.length &gt; 5">
                        <button class="more-btn" t-on-click="() => this.openCategoryPopup()">
                            View More (<t t-out="this.state.categories.length - 5"/>)
                        </button>
                    </div>
                </div>

                <!-- TOP CASHIERS -->
                <div class="data-card">
                    <div class="data-title top-product-header">
                        <span>👨‍💼 Top Cashiers</span>
                    </div>
                    <table class="modern-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Cashier</th>
                                <th>Orders</th>
                                <th>Sales</th>
                            </tr>
                        </thead>
                        <tbody>
                            <t t-foreach="this.state.top_cashiers.slice(0,5)" t-as="c" t-key="c.id">
                                <tr>
                                    <td><t t-out="c.rank"/></td>
                                    <td style="display:flex; align-items:center; gap:10px;">
                                        <div class="customer-img-wrapper">
                                            <img t-att-src="'/web/image/' + (c.model || 'hr.employee') + '/' + c.id + '/image_128'" class="customer-avatar"/>
                                            <img t-att-src="'/web/image/' + (c.model || 'hr.employee') + '/' + c.id + '/image_128'" class="customer-zoom"/>
                                        </div>
                                        <span><t t-out="c.name"/></span>
                                    </td>
                                    <td><t t-out="c.orders"/> Orders</td>
                                    <td class="sales-value">
                                        <t t-out="this.state.currency.symbol"/> <t t-out="c.sales"/>
                                    </td>
                                </tr>
                            </t>
                        </tbody>
                    </table>

                    <div class="session-more" t-if="this.state.top_cashiers.length &gt; 5">
                        <button class="more-btn" t-on-click="() => this.openCashierPopup()">
                            View More (<t t-out="this.state.top_cashiers.length - 5"/>)
                        </button>
                    </div>
                </div>
            </div>

            <!-- ================= POPUPS ================= -->
            <t t-if="this.state.showProductPopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeProductPopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>All Top Selling Products</span>
                            <button class="popup-close" t-on-click="() => this.closeProductPopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.products.slice(5)" t-as="p" t-key="p[2]">
                                    <tr>
                                        <td><t t-out="p[0]"/></td>
                                        <td><span class="qty-pill"><t t-out="p[1]"/></span></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showSessionPopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeSessionPopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>All Active Sessions</span>
                            <button class="popup-close" t-on-click="() => this.closeSessionPopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Session</th>
                                    <th>Cashier</th>
                                    <th>Store</th>
                                    <th>Opening Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.sessions.slice(5)" t-as="s" t-key="s.id">
                                    <tr>
                                        <td><t t-out="s.name"/></td>
                                        <td><t t-out="s.user"/></td>
                                        <td><t t-out="s.config"/></td>
                                        <td><t t-out="s.start_at"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showProductDetails">
                <div class="session-popup-overlay" t-on-click="() => this.closeProductDetails()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>Product Sales Details</span>
                            <button class="popup-close" t-on-click="() => this.closeProductDetails()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Order</th>
                                    <th>Date</th>
                                    <th>Qty</th>
                                    <th>Unit Price</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.product_details" t-as="d" t-key="d.id">
                                    <tr>
                                        <td><t t-out="d.order"/></td>
                                        <td><t t-out="d.date"/></td>
                                        <td><t t-out="d.qty"/></td>
                                        <td><t t-out="this.state.currency.symbol"/> <t t-out="d.price"/></td>
                                        <td class="sales-value"><t t-out="this.state.currency.symbol"/> <t t-out="d.total"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showStorePopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeStorePopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>All Store Performance</span>
                            <button class="popup-close" t-on-click="() => this.closeStorePopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Store</th>
                                    <th>Orders</th>
                                    <th>Sales</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-set="rank" t-value="4"/>
                                <t t-foreach="this.state.stores.slice(3)" t-as="s" t-key="s[0]">
                                    <tr>
                                        <td><t t-out="rank"/></td>
                                        <td><t t-out="s[0]"/></td>
                                        <td><t t-out="s[1]"/> Orders</td>
                                        <td class="sales-value"><t t-out="this.state.currency.symbol"/> <t t-out="s[2]"/></td>
                                    </tr>
                                    <t t-set="rank" t-value="rank + 1"/>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showCategoryPopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeCategoryPopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>Top Categories</span>
                            <button class="popup-close" t-on-click="() => this.closeCategoryPopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.categories.slice(5)" t-as="cat" t-key="cat.id">
                                    <tr>
                                        <td><t t-out="cat.name"/></td>
                                        <td><span class="qty-pill"><t t-out="cat.qty"/></span></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showCategoryProducts">
                <div class="session-popup-overlay" t-on-click="() => this.closeCategoryProducts()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>Category Products</span>
                            <button class="popup-close" t-on-click="() => this.closeCategoryProducts()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.category_products" t-as="p" t-key="p.id">
                                    <tr>
                                        <td><t t-out="p.name"/></td>
                                        <td><span class="qty-pill"><t t-out="p.qty"/></span></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showCustomerPopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeCustomerPopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>Top Customers</span>
                            <button class="popup-close" t-on-click="() => this.closeCustomerPopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Customer</th>
                                    <th>Sales</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.customers.slice(5)" t-as="c" t-key="c[0]">
                                    <tr>
                                        <td style="display:flex; align-items:center; gap:10px;">
                                            <div class="customer-img-wrapper">
                                                <img t-att-src="'/web/image/res.partner/' + c[0] + '/image_128'" class="customer-avatar"/>
                                                <img t-att-src="'/web/image/res.partner/' + c[0] + '/image_128'" class="customer-zoom"/>
                                            </div>
                                            <span><t t-out="c[1]"/></span>
                                        </td>
                                        <td class="sales-value"><t t-out="this.state.currency.symbol"/> <t t-out="c[2]"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

            <t t-if="this.state.showCashierPopup">
                <div class="session-popup-overlay" t-on-click="() => this.closeCashierPopup()">
                    <div class="session-popup" t-on-click.stop="">
                        <div class="popup-header">
                            <span>Top Cashiers</span>
                            <button class="popup-close" t-on-click="() => this.closeCashierPopup()">✕</button>
                        </div>
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Cashier</th>
                                    <th>Orders</th>
                                    <th>Sales</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="this.state.top_cashiers.slice(5)" t-as="c" t-key="c.id">
                                    <tr>
                                        <td><t t-out="c.rank"/></td>
                                        <td><t t-out="c.name"/></td>
                                        <td><t t-out="c.orders"/></td>
                                        <td class="sales-value"><t t-out="this.state.currency.symbol"/> <t t-out="c.sales"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </div>
                </div>
            </t>

        </div>
    </t>
</templates>
```

# views\dashboard_view.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <record id="action_pos_dashboard" model="ir.actions.client">
        <field name="name">POS Dashboard</field>
        <field name="tag">pos_dashboard</field>
    </record>

    <menuitem id="menu_pos_dashboard"
              name="POS Dashboard"
              parent="point_of_sale.menu_point_root"
              action="action_pos_dashboard"
              sequence="2"
              groups="point_of_sale.group_pos_manager"/>

</odoo>

```

