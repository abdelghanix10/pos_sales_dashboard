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

