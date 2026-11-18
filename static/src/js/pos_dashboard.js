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
    const tickColor = this.state.dark_mode ? "#94a3b8" : "#64748b";
    const gridColor = this.state.dark_mode ? "#334155" : "#e2e8f0";

    this.salesTrendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Sales",
            data: values,
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79, 70, 229, 0.12)",
            fill: true,
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: tickColor },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: { color: tickColor },
            grid: { color: gridColor },
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
    const tickColor = this.state.dark_mode ? "#94a3b8" : "#64748b";
    const gridColor = this.state.dark_mode ? "#334155" : "#e2e8f0";

    this.productChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Qty Sold",
            data: qtyValues,
            backgroundColor: [
              "#4f46e5",
              "#10b981",
              "#f59e0b",
              "#8b5cf6",
              "#0ea5e9",
            ],
            borderRadius: 6,
            barPercentage: 0.55,
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
              color: tickColor,
              autoSkip: false,
              maxRotation: 35,
              minRotation: 20,
              font: { size: 11 },
            },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: tickColor,
              font: { size: 11 },
            },
            grid: {
              color: gridColor,
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
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: [
              "#4f46e5",
              "#10b981",
              "#f59e0b",
              "#8b5cf6",
              "#0ea5e9",
            ],
            borderWidth: 2,
            borderColor: this.state.dark_mode ? "#1e293b" : "#ffffff",
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
              color: this.state.dark_mode ? "#cbd5e1" : "#475569",
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
    const tickColor = this.state.dark_mode ? "#94a3b8" : "#64748b";
    const gridColor = this.state.dark_mode ? "#334155" : "#e2e8f0";

    this.storeComparisonChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Current Period",
            data: current,
            backgroundColor: "#4f46e5",
            borderRadius: 5,
          },
          {
            label: "Previous Period",
            data: previous,
            backgroundColor: "#94a3b8",
            borderRadius: 5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: tickColor },
          },
        },
        scales: {
          x: {
            ticks: { color: tickColor },
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            ticks: { color: tickColor },
            grid: { color: gridColor },
          },
        },
      },
    });
  }
}

registry.category("actions").add("pos_dashboard", PosDashboard);
