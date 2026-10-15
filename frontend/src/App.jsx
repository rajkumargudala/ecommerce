import React, { useEffect, useMemo, useState } from "react";
import { request, URLs } from "./api.js";

const money = (n) => `$${Number(n || 0).toFixed(2)}`;

export default function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("poly_user") || "null"));
  const [tab, setTab] = useState("overview");

  // Domain data states
  const [products, setProducts] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [orders, setOrders] = useState([]);
  const [payments, setPayments] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [snapshots, setSnapshots] = useState([]);

  // UI state
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [error, setError] = useState("");
  const [toasts, setToasts] = useState([]);
  const [isNewProductOpen, setIsNewProductOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState({});
  const [isRefreshing, setIsRefreshing] = useState(false);

  const addToast = (message, type = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3200);
  };

  async function loadAll() {
    setIsRefreshing(true);
    setError("");

    const services = [
      { name: "Catalog", key: "catalog", url: `${URLs.catalog}/products`, setter: setProducts },
      { name: "Inventory", key: "inventory", url: `${URLs.inventory}/inventory`, setter: setInventory },
      { name: "Orders", key: "orders", url: `${URLs.orders}/orders`, setter: setOrders },
      { name: "Payments", key: "payments", url: `${URLs.payments}/payments`, setter: setPayments },
      {
        name: "Notifications",
        key: "notifications",
        url: `${URLs.notifications}/notifications${user?.email ? `?recipient=${encodeURIComponent(user.email)}` : ""}`,
        setter: setNotifications,
      },
      { name: "Analytics", key: "analytics", url: `${URLs.analytics}/analytics/summary`, setter: setAnalytics },
      { name: "Cart", key: "cart", url: `${URLs.cart}/health` },
      { name: "Shipping", key: "shipping", url: `${URLs.shipping}/health` },
      { name: "Reviews", key: "reviews", url: `${URLs.reviews}/health` },
      { name: "Promotions", key: "promotions", url: `${URLs.promotions}/health` },
      { name: "Search", key: "search", url: `${URLs.search}/health` },
    ];

    const results = await Promise.allSettled(services.map((s) => request(s.url)));
    const newHealth = {};
    const failed = [];

    results.forEach((res, idx) => {
      const s = services[idx];
      if (res.status === "fulfilled") {
        s.setter?.(res.value);
        newHealth[s.key] = true;
      } else {
        newHealth[s.key] = false;
        failed.push(`${s.name}: ${res.reason?.message || "Unavailable"}`);
      }
    });

    // Also check auth health
    request(`${URLs.auth}/health`)
      .then(() => {
        newHealth.auth = true;
      })
      .catch(() => {
        newHealth.auth = false;
      });

    setHealthStatus(newHealth);

    // Fetch snapshot history
    request(`${URLs.analytics}/analytics/snapshots`)
      .then((data) => {
        if (data?.snapshots) setSnapshots(data.snapshots);
      })
      .catch(() => {});

    if (failed.length > 0) {
      setError(failed.join(" | "));
    }
    setIsRefreshing(false);
  }

  useEffect(() => {
    if (!user) return;
    const token = localStorage.getItem("poly_token");
    if (token) {
      request(`${URLs.auth}/auth/me?token=${encodeURIComponent(token)}`).catch(() => {
        localStorage.clear();
        setUser(null);
      });
    }
    loadAll();
  }, [user]);

  if (!user) {
    return (
      <Login
        onLogin={(u, t) => {
          localStorage.setItem("poly_user", JSON.stringify(u));
          localStorage.setItem("poly_token", t);
          setUser(u);
        }}
      />
    );
  }

  // Cart operations
  const addToCart = (product) => {
    setCart((curr) => {
      const found = curr.find((x) => x.id === product.id);
      if (found) {
        return curr.map((x) => (x.id === product.id ? { ...x, quantity: x.quantity + 1 } : x));
      }
      return [...curr, { ...product, quantity: 1 }];
    });
    addToast(`Added "${product.name}" to cart`, "success");
  };

  const updateCartQty = (productId, delta) => {
    setCart((curr) =>
      curr
        .map((x) => {
          if (x.id === productId) {
            const next = x.quantity + delta;
            return next > 0 ? { ...x, quantity: next } : null;
          }
          return x;
        })
        .filter(Boolean)
    );
  };

  const removeCartItem = (productId) => {
    setCart((curr) => curr.filter((x) => x.id !== productId));
    addToast("Item removed from cart", "info");
  };

  const checkout = async () => {
    if (!cart.length) return;
    try {
      const order = await request(`${URLs.orders}/orders`, {
        method: "POST",
        body: JSON.stringify({
          user_email: user.email,
          items: cart.map((x) => ({ product_id: x.id, quantity: x.quantity })),
        }),
      });
      setCart([]);
      setIsCartOpen(false);
      await loadAll();
      setTab("orders");
      addToast(`Order #${order.id} created successfully!`, "success");
    } catch (e) {
      setError(e.message);
      addToast(`Order creation failed: ${e.message}`, "error");
    }
  };

  // Order & Payment Lifecycle
  const payOrder = async (order) => {
    try {
      await request(`${URLs.payments}/payments`, {
        method: "POST",
        body: JSON.stringify({
          orderId: order.id,
          amount: Number(order.total),
          method: "CARD",
          recipient: user.email,
        }),
      });
      await loadAll();
      addToast(`Payment captured for Order #${order.id}`, "success");
    } catch (e) {
      setError(e.message);
      addToast(`Payment failed: ${e.message}`, "error");
    }
  };

  const advanceOrderStatus = async (order) => {
    const nextStatus = order.status === "PAID" ? "PROCESSING" : order.status === "PROCESSING" ? "SHIPPED" : null;
    if (!nextStatus) return;
    try {
      await request(`${URLs.orders}/orders/${order.id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: nextStatus }),
      });
      await loadAll();
      addToast(`Order #${order.id} transitioned to ${nextStatus}`, "success");
    } catch (e) {
      setError(e.message);
      addToast(`Status update failed: ${e.message}`, "error");
    }
  };

  const cancelOrder = async (order) => {
    try {
      await request(`${URLs.orders}/orders/${order.id}/status`, {
        method: "PUT",
        body: JSON.stringify({ status: "CANCELLED" }),
      });
      await loadAll();
      addToast(`Order #${order.id} cancelled. Inventory reservation released.`, "info");
    } catch (e) {
      setError(e.message);
      addToast(e.message, "error");
    }
  };

  const refundPayment = async (payment) => {
    try {
      await request(`${URLs.payments}/payments/${payment.id}/refund`, { method: "POST" });
      await loadAll();
      addToast(`Payment #${payment.id} refunded. Order updated.`, "info");
    } catch (e) {
      setError(e.message);
      addToast(e.message, "error");
    }
  };

  const adjustStock = async (productId, delta) => {
    try {
      await request(`${URLs.inventory}/inventory/${productId}/adjust`, {
        method: "POST",
        body: JSON.stringify({ delta }),
      });
      await loadAll();
      addToast(`Stock for Product #${productId} updated (${delta > 0 ? `+${delta}` : delta})`, "success");
    } catch (e) {
      setError(e.message);
      addToast(e.message, "error");
    }
  };

  const markNotificationRead = async (id) => {
    try {
      await request(`${URLs.notifications}/notifications/${id}/read`, { method: "POST" });
      await loadAll();
    } catch (e) {
      setError(e.message);
    }
  };

  const markAllNotificationsRead = async () => {
    const unread = notifications.filter((n) => !n.is_read);
    for (const n of unread) {
      await request(`${URLs.notifications}/notifications/${n.id}/read`, { method: "POST" }).catch(() => {});
    }
    await loadAll();
    addToast("All notifications marked as read", "info");
  };

  const saveAnalyticsSnapshot = async () => {
    try {
      const snap = await request(`${URLs.analytics}/analytics/snapshot`, { method: "POST" });
      await loadAll();
      addToast(`Analytics snapshot #${snap.id} saved to analytics_db!`, "success");
    } catch (e) {
      setError(e.message);
      addToast(`Snapshot failed: ${e.message}`, "error");
    }
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
  };

  const unreadCount = notifications.filter((x) => !x.is_read).length;
  const lowStockCount = inventory.filter((x) => x.low_stock).length;
  const totalCartUnits = cart.reduce((s, x) => s + x.quantity, 0);
  const cartSubtotal = cart.reduce((s, x) => s + x.price * x.quantity, 0);

  const navItems = [
    { key: "overview", icon: "◈", label: "Overview" },
    { key: "catalog", icon: "◫", label: "Product Catalog" },
    { key: "orders", icon: "◎", label: "Orders & Cart", badge: orders.length || null },
    { key: "inventory", icon: "▦", label: "Inventory", badge: lowStockCount ? `${lowStockCount} low` : null },
    { key: "payments", icon: "◇", label: "Payment Ledger" },
    { key: "notifications", icon: "◌", label: "Notifications", badge: unreadCount || null },
    { key: "analytics", icon: "⌁", label: "Analytics BI" },
    { key: "topology", icon: "☸", label: "EKS & Dedicated DBs" },
  ];

  return (
    <div className="app-shell">
      {/* Toast Notification Container */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className="toast-item">
            <span>{t.type === "success" ? "✓" : t.type === "error" ? "⚠" : "✦"}</span>
            {t.message}
          </div>
        ))}
      </div>

      {/* Global Cart Slide-Over Drawer */}
      {isCartOpen && (
        <div className="cart-drawer-overlay" onClick={() => setIsCartOpen(false)}>
          <div className="cart-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="eyebrow">YOUR BASKET</span>
                <h3>Shopping Cart ({totalCartUnits})</h3>
              </div>
              <button className="btn btn-secondary btn-icon" onClick={() => setIsCartOpen(false)}>
                ✕
              </button>
            </div>

            <div className="cart-lines">
              {cart.map((item) => (
                <div key={item.id} className="cart-item">
                  <div className="cart-item-icon">{item.image}</div>
                  <div>
                    <strong style={{ fontSize: 13, display: "block" }}>{item.name}</strong>
                    <small style={{ color: "var(--text-muted)" }}>{money(item.price)} each</small>
                  </div>
                  <div className="cart-qty-ctrl">
                    <button onClick={() => updateCartQty(item.id, -1)}>−</button>
                    <span style={{ fontSize: 12, fontWeight: 700 }}>{item.quantity}</span>
                    <button onClick={() => updateCartQty(item.id, 1)}>+</button>
                  </div>
                  <button className="btn btn-danger btn-sm" onClick={() => removeCartItem(item.id)}>
                    ✕
                  </button>
                </div>
              ))}
              {!cart.length && (
                <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-faint)" }}>
                  <div style={{ fontSize: 40, marginBottom: 10 }}>🛍️</div>
                  <p>Your cart is empty.</p>
                  <small>Add items from the Product Catalog to checkout.</small>
                </div>
              )}
            </div>

            {cart.length > 0 && (
              <div className="drawer-footer">
                <div className="bill-line">
                  <span>Subtotal</span>
                  <strong>{money(cartSubtotal)}</strong>
                </div>
                <div className="bill-line">
                  <span>Estimated Tax (8%)</span>
                  <span>{money(cartSubtotal * 0.08)}</span>
                </div>
                <div className="bill-line total">
                  <span>Total Amount</span>
                  <strong>{money(cartSubtotal * 1.08)}</strong>
                </div>
                <button className="btn btn-primary" style={{ width: "100%", padding: 14 }} onClick={checkout}>
                  Place Order ({money(cartSubtotal * 1.08)}) →
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: New Product Creation */}
      {isNewProductOpen && (
        <NewProductModal
          onClose={() => setIsNewProductOpen(false)}
          onCreate={async (productData) => {
            try {
              const created = await request(`${URLs.catalog}/products`, {
                method: "POST",
                body: JSON.stringify({
                  name: productData.name,
                  category: productData.category,
                  description: productData.description,
                  price: Number(productData.price),
                  image: productData.image,
                  active: true,
                }),
              });
              // Seed inventory immediately
              await request(`${URLs.inventory}/inventory/${created.id}/adjust`, {
                method: "POST",
                body: JSON.stringify({ delta: Number(productData.initialStock) || 20 }),
              });
              setIsNewProductOpen(false);
              await loadAll();
              addToast(`Product "${created.name}" created and stock initialized!`, "success");
            } catch (e) {
              setError(e.message);
              addToast(e.message, "error");
            }
          }}
        />
      )}

      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">DS</div>
          <div className="brand-meta">
            <strong>Polyglot Commerce</strong>
            <small>DevOps Shack · AWS EKS</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${tab === item.key ? "active" : ""}`}
              onClick={() => setTab(item.key)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="eks-badge">
            <div className="eks-badge-header">
              <span className="pulse-dot" />
              AWS EKS + ArgoCD
            </div>
            <small>GitOps Active · Helm v2.0</small>
            <small>7 Decoupled Dedicated DBs</small>
          </div>
        </div>
      </aside>

      {/* Main Workspace Area */}
      <main className="workspace">
        <header className="top-header">
          <div className="header-title-box">
            <span className="eyebrow">ENTERPRISE MICROSERVICE CONTROL CENTER</span>
            <h1>{navItems.find((x) => x.key === tab)?.label}</h1>
          </div>

          <div className="header-actions">
            <button className="btn btn-secondary" onClick={loadAll} disabled={isRefreshing}>
              {isRefreshing ? "↻ Refreshing..." : "↻ Refresh Cluster"}
            </button>

            <button className="cart-btn" onClick={() => setIsCartOpen(true)}>
              <span>🛒</span>
              Cart
              {totalCartUnits > 0 && <span className="cart-badge">{totalCartUnits}</span>}
            </button>

            <div className="user-profile">
              <div className="avatar">{user.name?.[0] || "U"}</div>
              <div className="user-meta">
                <strong>{user.name}</strong>
                <small>{user.email}</small>
              </div>
            </div>

            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Sign out
            </button>
          </div>
        </header>

        {error && (
          <div className="card" style={{ borderColor: "var(--accent-danger)", background: "rgba(239,68,68,0.1)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#fca5a5", fontSize: 13, fontWeight: 600 }}>⚠ {error}</span>
              <button className="btn btn-secondary btn-sm" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Tab 1: Overview Dashboard */}
        {tab === "overview" && (
          <>
            <section className="hero-card card">
              <div className="hero-content">
                <span className="pill pill-blue">ENTERPRISE CLOUD ARCHITECTURE</span>
                <h2>Production Polyglot Microservices on AWS EKS</h2>
                <p>
                  Seven independent microservices, each operating its own dedicated PostgreSQL database with fault domain
                  isolation, automated GitOps reconciliation via ArgoCD, and Helm package management.
                </p>
                <div className="hero-actions">
                  <button className="btn btn-primary" onClick={() => setTab("catalog")}>
                    Explore Catalog →
                  </button>
                  <button className="btn btn-secondary" onClick={() => setTab("topology")}>
                    Inspect EKS Topology
                  </button>
                </div>
              </div>

              <div className="hero-diagram">
                <div className="diagram-header">
                  <span>DECOUPLED DATABASE ARCHITECTURE</span>
                  <span>100% ISOLATED</span>
                </div>
                <div className="diagram-grid">
                  <div className="diagram-node">
                    <strong>Auth :8081</strong>
                    <small>➔ auth-db:5432</small>
                  </div>
                  <div className="diagram-node">
                    <strong>Catalog :8082</strong>
                    <small>➔ catalog-db:5432</small>
                  </div>
                  <div className="diagram-node">
                    <strong>Inventory :8083</strong>
                    <small>➔ inventory-db:5432</small>
                  </div>
                  <div className="diagram-node">
                    <strong>Orders :8084</strong>
                    <small>➔ order-db:5432</small>
                  </div>
                  <div className="diagram-node">
                    <strong>Payments :8085</strong>
                    <small>➔ payment-db:5432</small>
                  </div>
                  <div className="diagram-node">
                    <strong>Notifications :8086</strong>
                    <small>➔ notification-db:5432</small>
                  </div>
                </div>
              </div>
            </section>

            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon-wrap" style={{ color: "var(--accent-success)", background: "rgba(16,185,129,0.1)" }}>
                  $
                </div>
                <div className="metric-body">
                  <span>CAPTURED REVENUE</span>
                  <strong>{money(analytics.captured_revenue)}</strong>
                  <small>{payments.length} ledger transaction(s)</small>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrap" style={{ color: "var(--accent-primary)", background: "rgba(59,130,246,0.1)" }}>
                  ◎
                </div>
                <div className="metric-body">
                  <span>TOTAL ORDERS</span>
                  <strong>{analytics.orders ?? orders.length}</strong>
                  <small>{orders.filter((x) => x.status === "PAID").length} paid & processed</small>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrap" style={{ color: "var(--accent-purple)", background: "rgba(139,92,246,0.1)" }}>
                  ◫
                </div>
                <div className="metric-body">
                  <span>ACTIVE SKUS</span>
                  <strong>{analytics.products ?? products.length}</strong>
                  <small>Go Catalog Service</small>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrap" style={{ color: "var(--accent-warning)", background: "rgba(245,158,11,0.1)" }}>
                  !
                </div>
                <div className="metric-body">
                  <span>LOW STOCK ALERTS</span>
                  <strong>{analytics.low_stock_count ?? lowStockCount}</strong>
                  <small>Node.js Inventory Service</small>
                </div>
              </div>
            </div>

            <div className="cols-2">
              <section className="card">
                <div className="panel-head">
                  <div>
                    <span className="eyebrow">RECENT ACTIVITY</span>
                    <h3>Latest Customer Orders</h3>
                  </div>
                  <button className="btn btn-secondary btn-sm" onClick={() => setTab("orders")}>
                    View All →
                  </button>
                </div>
                <OrderTable
                  orders={orders.slice(0, 5)}
                  pay={payOrder}
                  cancel={cancelOrder}
                  advance={advanceOrderStatus}
                />
              </section>

              <section className="card">
                <div className="panel-head">
                  <div>
                    <span className="eyebrow">CLUSTER HEALTH</span>
                    <h3>Microservices & Dedicated DB Matrix</h3>
                  </div>
                </div>
                <DedicatedDatabaseMatrix healthStatus={healthStatus} />
              </section>
            </div>
          </>
        )}

        {/* Tab 2: Product Catalog */}
        {tab === "catalog" && (
          <CatalogView
            products={products}
            inventory={inventory}
            onAddToCart={addToCart}
            onOpenNewProductModal={() => setIsNewProductOpen(true)}
          />
        )}

        {/* Tab 3: Orders & Tracking */}
        {tab === "orders" && (
          <OrdersView
            orders={orders}
            onPay={payOrder}
            onCancel={cancelOrder}
            onAdvance={advanceOrderStatus}
            onOpenCart={() => setIsCartOpen(true)}
          />
        )}

        {/* Tab 4: Inventory Management */}
        {tab === "inventory" && (
          <InventoryView
            inventory={inventory}
            products={products}
            onAdjustStock={adjustStock}
          />
        )}

        {/* Tab 5: Payment Ledger */}
        {tab === "payments" && (
          <PaymentsView
            payments={payments}
            capturedRevenue={analytics.captured_revenue}
            refundedAmount={analytics.refunded_amount}
            onRefund={refundPayment}
          />
        )}

        {/* Tab 6: Notifications Inbox */}
        {tab === "notifications" && (
          <NotificationsView
            notifications={notifications}
            onMarkRead={markNotificationRead}
            onMarkAllRead={markAllNotificationsRead}
          />
        )}

        {/* Tab 7: Analytics BI */}
        {tab === "analytics" && (
          <AnalyticsView
            analytics={analytics}
            snapshots={snapshots}
            onSaveSnapshot={saveAnalyticsSnapshot}
          />
        )}

        {/* Tab 8: EKS & Dedicated DB Topology */}
        {tab === "topology" && <TopologyView healthStatus={healthStatus} />}
      </main>
    </div>
  );
}

// ----------------------------------------------------
// Sub-views & Components
// ----------------------------------------------------

function DedicatedDatabaseMatrix({ healthStatus }) {
  const serviceMatrix = [
    { name: "Auth Service", lang: "Java 21", port: 8081, dbHost: "auth-db:5432", dbName: "auth_db", key: "auth" },
    { name: "Catalog Service", lang: "Go 1.22", port: 8082, dbHost: "catalog-db:5432", dbName: "catalog_db", key: "catalog" },
    { name: "Inventory Service", lang: "Node 20", port: 8083, dbHost: "inventory-db:5432", dbName: "inventory_db", key: "inventory" },
    { name: "Order Service", lang: "Python 3.11", port: 8084, dbHost: "order-db:5432", dbName: "order_db", key: "orders" },
    { name: "Payment Service", lang: "C# .NET 8", port: 8085, dbHost: "payment-db:5432", dbName: "payment_db", key: "payments" },
    { name: "Notify Service", lang: "Ruby 3.2", port: 8086, dbHost: "notification-db:5432", dbName: "notification_db", key: "notifications" },
    { name: "Analytics Service", lang: "PHP 8.2", port: 8087, dbHost: "analytics-db:5432", dbName: "analytics_db", key: "analytics" },
    { name: "Cart Service", lang: "Python 3.11 / FastAPI", port: 8088, dbHost: "cart-db:5432", dbName: "cart_db", key: "cart" },
    { name: "Shipping Service", lang: "Python 3.11 / FastAPI", port: 8089, dbHost: "shipping-db:5432", dbName: "shipping_db", key: "shipping" },
    { name: "Reviews Service", lang: "Python 3.11 / FastAPI", port: 8090, dbHost: "reviews-db:5432", dbName: "reviews_db", key: "reviews" },
    { name: "Promotions Service", lang: "Python 3.11 / FastAPI", port: 8091, dbHost: "promotions-db:5432", dbName: "promotions_db", key: "promotions" },
    { name: "Search Service", lang: "Python 3.11 / FastAPI", port: 8092, dbHost: "search-db:5432", dbName: "search_db", key: "search" },
  ];

  return (
    <div className="matrix-grid">
      {serviceMatrix.map((item) => (
        <div key={item.name} className="matrix-row">
          <span
            className="pulse-dot"
            style={{
              background: healthStatus[item.key] === false ? "var(--accent-danger)" : "var(--accent-success)",
              boxShadow: `0 0 8px ${healthStatus[item.key] === false ? "var(--accent-danger)" : "var(--accent-success)"}`,
            }}
          />
          <strong style={{ color: "#fff" }}>{item.name}</strong>
          <span className="tag-lang">{item.lang}</span>
          <code style={{ fontSize: 11, color: "var(--text-muted)" }}>:{item.port}</code>
          <span className="matrix-db-pill">{item.dbHost}</span>
          <span className="pill pill-green" style={{ fontSize: 9 }}>gp3</span>
        </div>
      ))}
    </div>
  );
}

function CatalogView({ products, inventory, onAddToCart, onOpenNewProductModal }) {
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("DEFAULT");

  const categories = useMemo(() => {
    const set = new Set(products.map((p) => p.category).filter(Boolean));
    return ["ALL", ...Array.from(set)];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products
      .filter((p) => {
        const matchesCat = selectedCategory === "ALL" || p.category.toLowerCase() === selectedCategory.toLowerCase();
        const matchesSearch = `${p.name} ${p.category} ${p.description}`
          .toLowerCase()
          .includes(searchQuery.toLowerCase());
        return matchesCat && matchesSearch;
      })
      .sort((a, b) => {
        if (sortBy === "PRICE_ASC") return a.price - b.price;
        if (sortBy === "PRICE_DESC") return b.price - a.price;
        if (sortBy === "NAME_ASC") return a.name.localeCompare(b.name);
        return 0;
      });
  }, [products, selectedCategory, searchQuery, sortBy]);

  return (
    <>
      <div className="catalog-toolbar">
        <div className="category-pills">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`cat-pill ${selectedCategory === cat ? "active" : ""}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="toolbar-controls">
          <input
            className="input-search"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <select className="select-sort" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="DEFAULT">Sort By: Featured</option>
            <option value="PRICE_ASC">Price: Low to High</option>
            <option value="PRICE_DESC">Price: High to Low</option>
            <option value="NAME_ASC">Name: A to Z</option>
          </select>
          <button className="btn btn-primary" onClick={onOpenNewProductModal}>
            + Add Product
          </button>
        </div>
      </div>

      <div className="product-grid">
        {filteredProducts.map((p) => {
          const inv = inventory.find((i) => Number(i.product_id) === p.id);
          const available = inv ? Number(inv.available) : 0;
          const isLow = inv ? inv.low_stock : false;

          return (
            <div key={p.id} className="product-card">
              <div className="product-top">
                <div className="product-icon">{p.image || "📦"}</div>
                {available <= 0 ? (
                  <span className="pill pill-red">Out of Stock</span>
                ) : isLow ? (
                  <span className="pill pill-amber">Low Stock ({available})</span>
                ) : (
                  <span className="pill pill-green">{available} Available</span>
                )}
              </div>

              <span className="product-category">{p.category}</span>
              <h3>{p.name}</h3>
              <p className="product-desc">{p.description}</p>

              <div className="product-bottom">
                <span className="product-price">{money(p.price)}</span>
                <button
                  className="btn btn-primary btn-sm"
                  disabled={available <= 0}
                  onClick={() => onAddToCart(p)}
                >
                  {available <= 0 ? "Sold Out" : "Add to Cart"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function OrdersView({ orders, onPay, onCancel, onAdvance, onOpenCart }) {
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [orderSearch, setOrderSearch] = useState("");

  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      const matchStatus = statusFilter === "ALL" || o.status === statusFilter;
      const matchSearch =
        String(o.id).includes(orderSearch) || o.user_email?.toLowerCase().includes(orderSearch.toLowerCase());
      return matchStatus && matchSearch;
    });
  }, [orders, statusFilter, orderSearch]);

  const statuses = ["ALL", "CREATED", "PAID", "PROCESSING", "SHIPPED", "CANCELLED", "REFUNDED"];

  return (
    <>
      <div className="catalog-toolbar">
        <div className="category-pills">
          {statuses.map((st) => (
            <button
              key={st}
              className={`cat-pill ${statusFilter === st ? "active" : ""}`}
              onClick={() => setStatusFilter(st)}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="toolbar-controls">
          <input
            className="input-search"
            placeholder="Search by Order ID or email..."
            value={orderSearch}
            onChange={(e) => setOrderSearch(e.target.value)}
          />
          <button className="btn btn-secondary" onClick={onOpenCart}>
            Open Cart Drawer
          </button>
        </div>
      </div>

      <div className="card">
        <OrderTable
          orders={filteredOrders}
          pay={onPay}
          cancel={onCancel}
          advance={onAdvance}
        />
      </div>
    </>
  );
}

function OrderTable({ orders, pay, cancel, advance }) {
  const getPill = (status) => {
    switch (status) {
      case "PAID":
        return <span className="pill pill-green">PAID</span>;
      case "PROCESSING":
        return <span className="pill pill-blue">PROCESSING</span>;
      case "SHIPPED":
        return <span className="pill pill-purple">SHIPPED</span>;
      case "REFUNDED":
        return <span className="pill pill-amber">REFUNDED</span>;
      case "CANCELLED":
        return <span className="pill pill-red">CANCELLED</span>;
      default:
        return <span className="pill pill-blue">CREATED</span>;
    }
  };

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Customer</th>
            <th>Total Value</th>
            <th>Status</th>
            <th>Lifecycle</th>
            <th>Items</th>
            <th style={{ textAlign: "right" }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>
                <strong style={{ color: "#fff" }}>#{o.id}</strong>
              </td>
              <td>{o.user_email}</td>
              <td>
                <strong style={{ color: "#fff" }}>{money(o.total)}</strong>
              </td>
              <td>{getPill(o.status)}</td>
              <td>
                <div className="order-stepper">
                  <span className={`step-dot ${["CREATED", "PAID", "PROCESSING", "SHIPPED"].includes(o.status) ? "done" : ""}`} />
                  <span className={`step-dot ${["PAID", "PROCESSING", "SHIPPED"].includes(o.status) ? "done" : ""}`} />
                  <span className={`step-dot ${["PROCESSING", "SHIPPED"].includes(o.status) ? "done" : ""}`} />
                  <span className={`step-dot ${o.status === "SHIPPED" ? "done" : ""}`} />
                </div>
              </td>
              <td>{o.items?.reduce((s, x) => s + x.quantity, 0) || 0} unit(s)</td>
              <td style={{ textAlign: "right" }}>
                <div style={{ display: "inline-flex", gap: 6 }}>
                  {o.status === "CREATED" && (
                    <>
                      <button className="btn btn-primary btn-sm" onClick={() => pay(o)}>
                        Pay ({money(o.total)})
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => cancel(o)}>
                        Cancel
                      </button>
                    </>
                  )}
                  {o.status === "PAID" && (
                    <button className="btn btn-secondary btn-sm" onClick={() => advance(o)}>
                      Mark Processing →
                    </button>
                  )}
                  {o.status === "PROCESSING" && (
                    <button className="btn btn-primary btn-sm" onClick={() => advance(o)}>
                      Ship Order ✈
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
          {!orders.length && (
            <tr>
              <td colSpan="7" className="empty-state">
                No orders found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function InventoryView({ inventory, products, onAdjustStock }) {
  const [filterLow, setFilterLow] = useState(false);

  const displayed = filterLow ? inventory.filter((x) => x.low_stock) : inventory;

  return (
    <>
      <div className="catalog-toolbar">
        <div className="category-pills">
          <button className={`cat-pill ${!filterLow ? "active" : ""}`} onClick={() => setFilterLow(false)}>
            All Stock Items ({inventory.length})
          </button>
          <button className={`cat-pill ${filterLow ? "active" : ""}`} onClick={() => setFilterLow(true)}>
            Low Stock Alerts ({inventory.filter((x) => x.low_stock).length})
          </button>
        </div>
      </div>

      <div className="stock-grid">
        {displayed.map((inv) => {
          const product = products.find((p) => p.id === Number(inv.product_id));
          const available = Number(inv.available);
          const total = Number(inv.quantity);
          const pct = total > 0 ? Math.min(100, Math.round((available / total) * 100)) : 0;

          return (
            <div key={inv.product_id} className="stock-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <span className="product-category">SKU #{inv.product_id}</span>
                  <h3 style={{ fontSize: 18, marginTop: 4 }}>{product?.name || "Catalog Product"}</h3>
                </div>
                <div style={{ fontSize: 32 }}>{product?.image || "📦"}</div>
              </div>

              <div className="stock-no">
                {available}
                <small style={{ fontSize: 13, color: "var(--text-muted)", marginLeft: 6 }}>available</small>
              </div>

              <div className="stock-bar-wrap">
                <div
                  className="stock-bar"
                  style={{
                    width: `${pct}%`,
                    background: inv.low_stock ? "var(--accent-warning)" : "var(--accent-success)",
                  }}
                />
              </div>

              <p style={{ fontSize: 12, color: "var(--text-faint)" }}>
                Total: {inv.quantity} · Reserved: {inv.reserved} · Reorder: {inv.reorder_level}
              </p>

              <div className="stock-adjust-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => onAdjustStock(inv.product_id, -5)}>
                  −5
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => onAdjustStock(inv.product_id, 1)}>
                  +1
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => onAdjustStock(inv.product_id, 10)}>
                  +10
                </button>
                <button className="btn btn-primary btn-sm" onClick={() => onAdjustStock(inv.product_id, 25)}>
                  Restock +25
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function PaymentsView({ payments, capturedRevenue, refundedAmount, onRefund }) {
  return (
    <>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-success)", background: "rgba(16,185,129,0.1)" }}>
            $
          </div>
          <div className="metric-body">
            <span>CAPTURED REVENUE</span>
            <strong>{money(capturedRevenue)}</strong>
            <small>C# ASP.NET Payment Service</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-warning)", background: "rgba(245,158,11,0.1)" }}>
            ↩
          </div>
          <div className="metric-body">
            <span>REFUNDED AMOUNT</span>
            <strong>{money(refundedAmount)}</strong>
            <small>Processed chargebacks</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-primary)", background: "rgba(59,130,246,0.1)" }}>
            ✓
          </div>
          <div className="metric-body">
            <span>LEDGER ENTRIES</span>
            <strong>{payments.length}</strong>
            <small>payment_db persistence</small>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="panel-head">
          <div>
            <span className="eyebrow">TRANSACTION LOG</span>
            <h3>Historical Payment Records</h3>
          </div>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tx ID</th>
                <th>Order Ref</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Transaction Token</th>
                <th>Created</th>
                <th style={{ textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>#{p.id}</strong>
                  </td>
                  <td>#{p.orderId}</td>
                  <td>
                    <strong style={{ color: "#fff" }}>{money(p.amount)}</strong>
                  </td>
                  <td>{p.method}</td>
                  <td>
                    <span className={`pill ${p.status === "CAPTURED" ? "pill-green" : "pill-amber"}`}>
                      {p.status}
                    </span>
                  </td>
                  <td>
                    <code style={{ fontSize: 11, color: "var(--accent-cyan)" }}>{p.transactionRef}</code>
                  </td>
                  <td style={{ fontSize: 11, color: "var(--text-faint)" }}>
                    {p.createdAt ? new Date(p.createdAt).toLocaleDateString() : "Just now"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {p.status === "CAPTURED" && (
                      <button className="btn btn-danger btn-sm" onClick={() => onRefund(p)}>
                        Refund
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {!payments.length && (
                <tr>
                  <td colSpan="8" className="empty-state">
                    No transactions recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function NotificationsView({ notifications, onMarkRead, onMarkAllRead }) {
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="card">
      <div className="panel-head">
        <div>
          <span className="eyebrow">RUBY NOTIFICATION SERVICE</span>
          <h3>Event Inbox ({notifications.length})</h3>
        </div>
        {unreadCount > 0 && (
          <button className="btn btn-secondary btn-sm" onClick={onMarkAllRead}>
            Mark All as Read
          </button>
        )}
      </div>

      <div className="notification-list">
        {notifications.map((n) => (
          <div key={n.id} className={`notice-item ${!n.is_read ? "unread" : ""}`}>
            <div className="notice-icon-box">
              {n.type === "PAYMENT" ? "$" : n.type === "ORDER" ? "◎" : n.type === "REFUND" ? "↩" : "✦"}
            </div>
            <div className="notice-body">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <strong>{n.subject}</strong>
                <span className="pill pill-blue" style={{ fontSize: 9 }}>
                  {n.type}
                </span>
                {!n.is_read && <span className="pill pill-green" style={{ fontSize: 9 }}>NEW</span>}
              </div>
              <p>{n.message}</p>
              <small>{n.created_at || "Recent"}</small>
            </div>
            {!n.is_read && (
              <button className="btn btn-secondary btn-sm" onClick={() => onMarkRead(n.id)}>
                Mark Read
              </button>
            )}
          </div>
        ))}
        {!notifications.length && (
          <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-faint)" }}>
            <p>No notifications in your inbox.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsView({ analytics, snapshots, onSaveSnapshot }) {
  const orderStatus = analytics.order_status || {};
  const maxStatus = Math.max(1, ...Object.values(orderStatus));

  return (
    <>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-success)", background: "rgba(16,185,129,0.1)" }}>
            $
          </div>
          <div className="metric-body">
            <span>GROSS ORDER VALUE</span>
            <strong>{money(analytics.gross_order_value)}</strong>
            <small>Average Order: {money(analytics.average_order_value)}</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-primary)", background: "rgba(59,130,246,0.1)" }}>
            ◎
          </div>
          <div className="metric-body">
            <span>CAPTURED REVENUE</span>
            <strong>{money(analytics.captured_revenue)}</strong>
            <small>Refunded: {money(analytics.refunded_amount)}</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-purple)", background: "rgba(139,92,246,0.1)" }}>
            Σ
          </div>
          <div className="metric-body">
            <span>TOTAL TRANSACTIONS</span>
            <strong>{analytics.payments || 0}</strong>
            <small>Across {analytics.orders || 0} orders</small>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ color: "var(--accent-cyan)", background: "rgba(6,182,212,0.1)" }}>
            ⌁
          </div>
          <div className="metric-body">
            <span>PERSISTED SNAPSHOTS</span>
            <strong>{snapshots.length}</strong>
            <small>analytics_db storage</small>
          </div>
        </div>
      </div>

      <div className="cols-2">
        <section className="card">
          <div className="panel-head">
            <div>
              <span className="eyebrow">ORDER LIFECYCLE BREAKDOWN</span>
              <h3>Distribution by Status</h3>
            </div>
            <button className="btn btn-primary btn-sm" onClick={onSaveSnapshot}>
              + Save Snapshot to DB
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {Object.entries(orderStatus).map(([st, cnt]) => (
              <div key={st} style={{ display: "grid", gridTemplateColumns: "110px 1fr 40px", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)" }}>{st}</span>
                <div style={{ height: 8, background: "var(--bg-app)", borderRadius: 99, overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${(cnt / maxStatus) * 100}%`,
                      background: "var(--accent-primary-gradient)",
                    }}
                  />
                </div>
                <strong style={{ fontSize: 12, textAlign: "right" }}>{cnt}</strong>
              </div>
            ))}
            {!Object.keys(orderStatus).length && (
              <p style={{ color: "var(--text-faint)", fontSize: 13 }}>No orders recorded yet.</p>
            )}
          </div>
        </section>

        <section className="card">
          <div className="panel-head">
            <div>
              <span className="eyebrow">ANALYTICS_DB HISTORY</span>
              <h3>Persisted Snapshots</h3>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 280, overflowY: "auto" }}>
            {snapshots.map((s) => (
              <div
                key={s.id}
                style={{
                  padding: 12,
                  background: "var(--bg-sidebar)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 10,
                  fontSize: 12,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <strong style={{ color: "#fff" }}>Snapshot #{s.id}</strong>
                  <small style={{ color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                    {new Date(s.created_at).toLocaleTimeString()}
                  </small>
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: 11 }}>
                  Revenue: {money(s.payload?.captured_revenue)} · Orders: {s.payload?.orders} · SKUs: {s.payload?.products}
                </div>
              </div>
            ))}
            {!snapshots.length && (
              <p style={{ color: "var(--text-faint)", fontSize: 12 }}>
                Click "+ Save Snapshot to DB" to persist current metrics into analytics_db.
              </p>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

function TopologyView({ healthStatus }) {
  const nodes = [
    { name: "Auth Service", lang: "Java 21 / Spring Boot", port: 8081, dbHost: "auth-db:5432", dbName: "auth_db", pvc: "auth-db-data (5Gi gp3)", key: "auth" },
    { name: "Catalog Service", lang: "Go 1.22", port: 8082, dbHost: "catalog-db:5432", dbName: "catalog_db", pvc: "catalog-db-data (5Gi gp3)", key: "catalog" },
    { name: "Inventory Service", lang: "Node.js 20 / Express", port: 8083, dbHost: "inventory-db:5432", dbName: "inventory_db", pvc: "inventory-db-data (5Gi gp3)", key: "inventory" },
    { name: "Order Service", lang: "Python 3.11 / FastAPI", port: 8084, dbHost: "order-db:5432", dbName: "order_db", pvc: "order-db-data (5Gi gp3)", key: "orders" },
    { name: "Payment Service", lang: "C# / ASP.NET Core 8", port: 8085, dbHost: "payment-db:5432", dbName: "payment_db", pvc: "payment-db-data (5Gi gp3)", key: "payments" },
    { name: "Notification Service", lang: "Ruby 3.2 / Sinatra", port: 8086, dbHost: "notification-db:5432", dbName: "notification_db", pvc: "notification-db-data (5Gi gp3)", key: "notifications" },
    { name: "Analytics Service", lang: "PHP 8.2", port: 8087, dbHost: "analytics-db:5432", dbName: "analytics_db", pvc: "analytics-db-data (5Gi gp3)", key: "analytics" },
    { name: "Cart Service", lang: "Python 3.11 / FastAPI", port: 8088, dbHost: "cart-db:5432", dbName: "cart_db", pvc: "cart-db-data (5Gi gp3)", key: "cart" },
    { name: "Shipping Service", lang: "Python 3.11 / FastAPI", port: 8089, dbHost: "shipping-db:5432", dbName: "shipping_db", pvc: "shipping-db-data (5Gi gp3)", key: "shipping" },
    { name: "Reviews Service", lang: "Python 3.11 / FastAPI", port: 8090, dbHost: "reviews-db:5432", dbName: "reviews_db", pvc: "reviews-db-data (5Gi gp3)", key: "reviews" },
    { name: "Promotions Service", lang: "Python 3.11 / FastAPI", port: 8091, dbHost: "promotions-db:5432", dbName: "promotions_db", pvc: "promotions-db-data (5Gi gp3)", key: "promotions" },
    { name: "Search Service", lang: "Python 3.11 / FastAPI", port: 8092, dbHost: "search-db:5432", dbName: "search_db", pvc: "search-db-data (5Gi gp3)", key: "search" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div className="card">
        <div className="panel-head">
          <div>
            <span className="eyebrow">AWS EKS ARCHITECTURAL MAP</span>
            <h3>Decoupled Microservices & Dedicated Database Topology</h3>
          </div>
          <span className="pill pill-green">GitOps Reconciled via ArgoCD</span>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
          Every microservice deployed onto Amazon EKS runs in an isolated container and connects exclusively to its own
          dedicated StatefulSet database instance. Persistent state is bound to independent AWS EBS gp3 volumes.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
          {nodes.map((n) => (
            <div
              key={n.name}
              style={{
                background: "var(--bg-sidebar)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                padding: 18,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: 15, color: "#fff" }}>{n.name}</strong>
                <span className="pill pill-blue">{n.lang}</span>
              </div>

              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Cluster Port: <code style={{ color: "var(--text-main)" }}>:{n.port}</code>
              </div>

              <div
                style={{
                  background: "var(--bg-app)",
                  padding: 12,
                  borderRadius: 8,
                  border: "1px solid var(--border-card)",
                }}
              >
                <div style={{ fontSize: 10, textTransform: "uppercase", color: "var(--text-faint)", fontWeight: 800 }}>
                  DEDICATED POSTGRES DATABASE
                </div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "var(--accent-cyan)", margin: "4px 0" }}>
                  {n.dbHost}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-faint)" }}>
                  Database: <code>{n.dbName}</code> · Storage: <code>{n.pvc}</code>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function NewProductModal({ onClose, onCreate }) {
  const [form, setForm] = useState({
    name: "",
    category: "Workspace",
    price: "49.99",
    image: "⚡",
    description: "",
    initialStock: "25",
  });

  const submit = (e) => {
    e.preventDefault();
    onCreate(form);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
          <h3>Add New Catalog SKU</h3>
          <button className="btn btn-secondary btn-icon" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={submit}>
          <div className="form-group">
            <label>Product Name</label>
            <input
              required
              placeholder="e.g. Kubernetes Cluster Keyring"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 12 }}>
            <div className="form-group">
              <label>Category</label>
              <input
                required
                placeholder="Workspace, Audio, Hardware..."
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Icon / Emoji</label>
              <input
                required
                placeholder="📦"
                value={form.image}
                onChange={(e) => setForm({ ...form, image: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="form-group">
              <label>Price ($ USD)</label>
              <input
                required
                type="number"
                step="0.01"
                min="0"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Initial Stock (Inventory DB)</label>
              <input
                required
                type="number"
                min="1"
                value={form.initialStock}
                onChange={(e) => setForm({ ...form, initialStock: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              rows={3}
              placeholder="Brief product specifications..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create SKU & Seed Stock
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "admin@devopsshack.com", password: "admin123" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await request(`${URLs.auth}/auth/register`, {
          method: "POST",
          body: JSON.stringify(form),
        });
      }
      const data = await request(`${URLs.auth}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ email: form.email, password: form.password }),
      });
      onLogin(data.user, data.token);
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-showcase">
        <div className="brand" style={{ border: "none" }}>
          <div className="brand-icon">DS</div>
          <div className="brand-meta">
            <strong style={{ fontSize: 18 }}>DevOps Shack</strong>
            <small>Enterprise Polyglot Platform</small>
          </div>
        </div>

        <div>
          <span className="pill pill-blue">AWS EKS GITOPS PLATFORM</span>
          <h1>Seven Polyglot Services.<br />Seven Dedicated Databases.</h1>
          <p style={{ color: "var(--text-muted)", fontSize: 15, lineHeight: 1.7, maxWidth: 520 }}>
            An enterprise microservices platform written across 7 major programming languages, deployed onto AWS EKS with
            Helm and ArgoCD GitOps reconciliation, and engineered with Database-per-Service fault isolation.
          </p>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 24 }}>
            {["Java 21", "Go 1.22", "Node.js 20", "Python 3.11", "C# .NET 8", "Ruby 3.2", "PHP 8.2"].map((lang) => (
              <span key={lang} className="tag-lang" style={{ padding: "6px 12px", fontSize: 11 }}>
                {lang}
              </span>
            ))}
          </div>
        </div>

        <div style={{ fontSize: 12, color: "var(--text-faint)" }}>
          Production Ready · Managed by Terraform & ArgoCD
        </div>
      </div>

      <div className="login-form-box">
        <div className="login-card">
          <span className="eyebrow">ENTERPRISE ACCESS</span>
          <h2>{mode === "login" ? "Sign in to Control Center" : "Create Developer Account"}</h2>

          {error && (
            <div
              style={{
                padding: "10px 14px",
                background: "rgba(239,68,68,0.1)",
                border: "1px solid var(--accent-danger)",
                borderRadius: 8,
                color: "#fca5a5",
                fontSize: 12,
                marginBottom: 16,
              }}
            >
              ⚠ {error}
            </div>
          )}

          <form onSubmit={submit}>
            {mode === "register" && (
              <div className="form-group">
                <label>Full Name</label>
                <input
                  required
                  placeholder="Platform Engineer"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
            )}

            <div className="form-group">
              <label>Work Email</label>
              <input
                required
                type="email"
                placeholder="admin@devopsshack.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                required
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%", padding: 12, marginTop: 8 }}
              disabled={loading}
            >
              {loading ? "Authenticating..." : mode === "login" ? "Sign In →" : "Register & Sign In →"}
            </button>

            <button
              type="button"
              style={{
                width: "100%",
                background: "transparent",
                color: "var(--accent-primary)",
                marginTop: 14,
                fontSize: 12,
                fontWeight: 600,
              }}
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Need an account? Register" : "Already registered? Sign In"}
            </button>
          </form>

          <div className="demo-account-box">
            <strong>Default Credentials:</strong>
            <div>Email: <code>admin@devopsshack.com</code></div>
            <div>Password: <code>admin123</code></div>
          </div>
        </div>
      </div>
    </div>
  );
}
