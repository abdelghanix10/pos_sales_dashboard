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