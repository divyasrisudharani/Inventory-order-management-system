import { useEffect, useState } from "react";
import api from "../services/api";
import "./ManageOrders.css";

function ManageOrders() {
  const [orders, setOrders] = useState([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedOrder, setExpandedOrder] = useState(null);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/orders");

      // OrderListResponse returns { orders: [], total_orders: number }
      const orderList = response.data.orders || [];

      setOrders(orderList);
      setTotalOrders(
        response.data.total_orders ?? orderList.length
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load orders. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const toggleOrderDetails = (orderId) => {
    setExpandedOrder((current) =>
      current === orderId ? null : orderId
    );
  };

  const formatDate = (date) => {
    if (!date) return "N/A";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "N/A";
    }

    return parsedDate.toLocaleString();
  };

  const formatAmount = (amount) => {
    return Number(amount || 0).toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    });
  };

  const getStatusClass = (status) => {
    switch (status?.toUpperCase()) {
      case "PENDING":
        return "pending";

      case "CONFIRMED":
        return "confirmed";

      case "CANCELLED":
        return "cancelled";

      case "DELIVERED":
        return "delivered";

      case "COMPLETED":
        return "completed";

      default:
        return "default";
    }
  };

  if (loading) {
    return (
      <div className="manage-orders-page">
        <p className="orders-message">Loading orders...</p>
      </div>
    );
  }

  return (
    <div className="manage-orders-page">
      <div className="orders-header">
        <div>
          <h1>Manage Orders</h1>
          <p>View and monitor customer orders</p>
        </div>

        <button
          className="refresh-orders-btn"
          onClick={fetchOrders}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="orders-summary">
        <div className="orders-summary-card">
          <span>Total Orders</span>
          <h2>{totalOrders}</h2>
        </div>

        <div className="orders-summary-card">
          <span>Pending Orders</span>
          <h2>
            {orders.filter(
              (order) => order.status === "PENDING"
            ).length}
          </h2>
        </div>

        <div className="orders-summary-card">
          <span>Confirmed Orders</span>
          <h2>
            {orders.filter(
              (order) => order.status === "CONFIRMED"
            ).length}
          </h2>
        </div>

        <div className="orders-summary-card">
          <span>Cancelled Orders</span>
          <h2>
            {orders.filter(
              (order) => order.status === "CANCELLED"
            ).length}
          </h2>
        </div>
      </div>

      {error && (
        <div className="orders-error">
          {error}
          <button onClick={fetchOrders}>Retry</button>
        </div>
      )}

      {!error && orders.length === 0 ? (
        <div className="orders-empty">
          <h3>No Orders Found</h3>
          <p>Customer orders will appear here.</p>
        </div>
      ) : (
        !error && (
          <div className="orders-table-container">
            <table className="orders-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer ID</th>
                  <th>Order Date</th>
                  <th>Total Amount</th>
                  <th>Status</th>
                  <th>Details</th>
                </tr>
              </thead>

              <tbody>
                {orders.map((order) => (
                  <>
                    <tr key={order.id}>
                      <td>#{order.id}</td>

                      <td>{order.user_id}</td>

                      <td>{formatDate(order.created_at)}</td>

                      <td className="order-amount">
                        {formatAmount(order.total_amount)}
                      </td>

                      <td>
                        <span
                          className={`order-status ${getStatusClass(
                            order.status
                          )}`}
                        >
                          {order.status}
                        </span>
                      </td>

                      <td>
                        <button
                          className="view-order-btn"
                          onClick={() =>
                            toggleOrderDetails(order.id)
                          }
                        >
                          {expandedOrder === order.id
                            ? "Hide"
                            : "View"}
                        </button>
                      </td>
                    </tr>

                    {expandedOrder === order.id && (
                      <tr key={`details-${order.id}`}>
                        <td colSpan="6">
                          <div className="order-details">
                            <h3>Order #{order.id} Details</h3>

                            <p>
                              <strong>Shipping Address:</strong>{" "}
                              {order.shipping_address || "N/A"}
                            </p>

                            <h4>Ordered Products</h4>

                            {order.items?.length > 0 ? (
                              <div className="order-items-table-wrapper">
                                <table className="order-items-table">
                                  <thead>
                                    <tr>
                                      <th>Product ID</th>
                                      <th>Product Name</th>
                                      <th>Quantity</th>
                                      <th>Unit Price</th>
                                      <th>Subtotal</th>
                                    </tr>
                                  </thead>

                                  <tbody>
                                    {order.items.map((item, index) => (
                                      <tr key={item.id ?? index}>
                                        <td>{item.product_id}</td>
                                        <td>{item.product_name}</td>
                                        <td>{item.quantity}</td>
                                        <td>
                                          {formatAmount(item.unit_price)}
                                        </td>
                                        <td>
                                          {formatAmount(item.subtotal)}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            ) : (
                              <p>No order items available.</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}

export default ManageOrders;