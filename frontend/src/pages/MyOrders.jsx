import { useEffect, useState } from "react";
import api from "../services/api";
import "./MyOrders.css";

function MyOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [paymentLoading, setPaymentLoading] = useState(null);
  const [cancelLoading, setCancelLoading] = useState(null);

  // Load customer orders
  const loadOrders = async () => {
    try {
      setLoading(true);

      const response = await api.get("/orders");

      const orderData = Array.isArray(response.data)
        ? response.data
        : response.data.orders || [];

      setOrders(orderData);

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
        "Unable to load orders."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  // Payment function
  const handlePayment = async (orderId) => {
    try {
      setPaymentLoading(orderId);
      setMessage("");

      const response = await api.post("/payments", {
        order_id: orderId,
        payment_method: "TEST",
      });

      setMessage(
        response.data.message || "Payment successful!"
      );

      await loadOrders();

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
        "Payment failed. Please try again."
      );
    } finally {
      setPaymentLoading(null);
    }
  };

  // Cancel order
  const handleCancel = async (orderId) => {
    const confirmed = window.confirm(
      "Are you sure you want to cancel this order?"
    );

    if (!confirmed) return;

    try {
      setCancelLoading(orderId);
      setMessage("");

      await api.post(`/orders/${orderId}/cancel`);

      setMessage("Order cancelled successfully!");

      await loadOrders();

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
        "Unable to cancel order."
      );
    } finally {
      setCancelLoading(null);
    }
  };

  if (loading) {
    return <div className="my-orders-container">
      Loading orders...
    </div>;
  }

  return (
    <div className="my-orders-container">

      <h1>My Orders</h1>

      {message && (
        <p className="order-message">
          {message}
        </p>
      )}

      {orders.length === 0 ? (
        <div className="empty-orders">
          <h2>No Orders Found</h2>
          <p>You have not placed any orders yet.</p>
        </div>
      ) : (
        <div className="orders-list">

          {orders.map((order) => (

            <div className="order-card" key={order.id}>

              <h3>Order #{order.id}</h3>

              <p>
                Status: <strong>{order.status}</strong>
              </p>

              <p>
                Date: {
                  order.created_at
                    ? new Date(order.created_at).toLocaleString()
                    : "Not available"
                }
              </p>

              <h4>Products</h4>

              {(order.items || order.products || []).map(
                (item, index) => (
                  <p key={item.product_id || index}>
                    {item.product_name || item.name}
                    {" × "}
                    {item.quantity}
                    {" - ₹"}
                    {Number(
                      item.subtotal ??
                      (Number(item.price || 0) *
                       Number(item.quantity || 0))
                    ).toLocaleString("en-IN")}
                  </p>
                )
              )}

              <h3>
                Total: ₹
                {Number(order.total_amount || 0)
                  .toLocaleString("en-IN")}
              </h3>

              {order.status === "PENDING" && (
                <div className="order-actions">

                  <button
                    className="pay-button"
                    onClick={() => handlePayment(order.id)}
                    disabled={
                      paymentLoading === order.id ||
                      cancelLoading === order.id
                    }
                  >
                    {paymentLoading === order.id
                      ? "Processing..."
                      : "Pay Now"}
                  </button>

                  <button
                    className="cancel-button"
                    onClick={() => handleCancel(order.id)}
                    disabled={
                      cancelLoading === order.id ||
                      paymentLoading === order.id
                    }
                  >
                    {cancelLoading === order.id
                      ? "Cancelling..."
                      : "Cancel Order"}
                  </button>

                </div>
              )}

            </div>
          ))}

        </div>
      )}

    </div>
  );
}

export default MyOrders;