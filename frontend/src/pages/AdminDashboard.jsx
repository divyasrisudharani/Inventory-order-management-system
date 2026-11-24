import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./AdminDashboard.css";

function AdminDashboard() {
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [productResponse, orderResponse] = await Promise.all([
        api.get("/products"),
        api.get("/orders"),
      ]);

      const productData = productResponse.data;
      const orderData = orderResponse.data;

      setProducts(
        Array.isArray(productData)
          ? productData
          : productData.products || []
      );

      setOrders(
        Array.isArray(orderData)
          ? orderData
          : orderData.orders || []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load dashboard data. Check your admin login and services."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const menuItems = [
    { title: "Manage Products", icon: "📦", path: "/admin/products" },
    { title: "Manage Inventory", icon: "🏬", path: "/admin/inventory" },
    { title: "Manage Orders", icon: "🛒", path: "/admin/orders" },
    { title: "Customers", icon: "👥", path: "/admin/customers" },
    { title: "Sales Analytics", icon: "📊", path: "/admin/analytics" },
    { title: "Manage Returns", icon: "↩️", path: "/admin/returns" },
  ];

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  if (loading) {
    return <div className="admin-container">Loading dashboard...</div>;
  }

  return (
    <div className="admin-container">
      <header className="admin-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Inventory and Order Management System</p>
        </div>

        <button onClick={logout} className="admin-logout">
          Logout
        </button>
      </header>

      {error && <p className="admin-error">{error}</p>}

      <section className="admin-stats">
        <div className="admin-stat-card">
          <h3>Total Products</h3>
          <p>{products.length}</p>
        </div>

        <div className="admin-stat-card">
          <h3>Total Orders</h3>
          <p>{orders.length}</p>
        </div>

        <div className="admin-stat-card">
          <h3>Pending Orders</h3>
          <p>
            {orders.filter(
              (order) => order.status?.toUpperCase() === "PENDING"
            ).length}
          </p>
        </div>

        <div className="admin-stat-card">
          <h3>Confirmed Orders</h3>
          <p>
            {orders.filter(
              (order) => order.status?.toUpperCase() === "CONFIRMED"
            ).length}
          </p>
        </div>
      </section>

      <div className="admin-section-heading">
        <h2>Management Sections</h2>
        <button onClick={loadDashboard}>Refresh Data</button>
      </div>

      <section className="admin-menu">
        {menuItems.map((item) => (
          <div className="admin-menu-card" key={item.path}>
            <span className="admin-menu-icon">{item.icon}</span>
            <h3>{item.title}</h3>
            <button onClick={() => navigate(item.path)}>
              Open
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}

export default AdminDashboard;