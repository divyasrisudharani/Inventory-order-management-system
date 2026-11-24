import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Checkout.css";

function Checkout() {
  const navigate = useNavigate();

  const [cart, setCart] = useState([]);
  const [shippingAddress, setShippingAddress] = useState("");
  const [loading, setLoading] = useState(true);
  const [placingOrder, setPlacingOrder] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const response = await api.get("/cart");
      setCart(response.data.items || []);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load cart."
      );
    } finally {
      setLoading(false);
    }
  };

  const totalAmount = cart.reduce((total, item) => {
    return total + Number(item.price || item.unit_price || 0) *
      Number(item.quantity || 0);
  }, 0);

  const placeOrder = async (e) => {
    e.preventDefault();

    if (!shippingAddress.trim()) {
      setError("Please enter your shipping address.");
      return;
    }

    if (cart.length === 0) {
      setError("Your cart is empty.");
      return;
    }

    try {
      setPlacingOrder(true);
      setError("");

      const response = await api.post("/orders", {
        shipping_address: shippingAddress.trim(),
      });

      setSuccess(response.data);

    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to place order."
      );
    } finally {
      setPlacingOrder(false);
    }
  };

  if (loading) {
    return <div className="checkout-container">Loading checkout...</div>;
  }

  if (success) {
    return (
      <div className="checkout-container">
        <div className="checkout-success">
          <h2>Order Placed Successfully!</h2>
          <p>Order ID: {success.id}</p>
          <p>Status: {success.status}</p>
          <p>Total: ₹{Number(success.total_amount).toLocaleString("en-IN")}</p>
          <button onClick={() => navigate("/orders")}>
            View My Orders
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-container">
      <h2>Checkout</h2>

      {error && <p className="checkout-error">{String(error)}</p>}

      <div className="checkout-layout">
        <div className="checkout-address">
          <h3>Shipping Address</h3>

          <form onSubmit={placeOrder}>
            <textarea
              placeholder="Enter your complete shipping address"
              value={shippingAddress}
              onChange={(e) => setShippingAddress(e.target.value)}
              rows="5"
              required
            />

            <button type="submit" disabled={placingOrder}>
              {placingOrder ? "Placing Order..." : "Place Order"}
            </button>
          </form>
        </div>

        <div className="checkout-summary">
          <h3>Order Summary</h3>

          {cart.map((item) => (
            <div className="checkout-item" key={item.id || item.product_id}>
              <span>{item.product_name || item.name}</span>
              <span>
                {item.quantity} × ₹
                {Number(item.price || item.unit_price || 0).toLocaleString("en-IN")}
              </span>
            </div>
          ))}

          <hr />

          <h3>
            Total: ₹{totalAmount.toLocaleString("en-IN")}
          </h3>
        </div>
      </div>
    </div>
  );
}

export default Checkout;