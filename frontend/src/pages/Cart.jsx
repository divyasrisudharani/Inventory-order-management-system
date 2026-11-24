import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Cart.css";

function Cart() {
  const navigate = useNavigate();

  const [cart, setCart] = useState({
    items: [],
    total_items: 0,
    total_amount: 0,
  });

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  // Load cart items
  const loadCart = async () => {
    try {
      setLoading(true);
      const response = await api.get("/cart");
      setCart(response.data);
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Unable to load cart."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, []);

  // Update quantity
  const updateQuantity = async (productId, quantity) => {
    if (quantity < 1) return;

    try {
      await api.put(`/cart/items/${productId}`, {
        quantity,
      });

      setMessage("Cart updated successfully!");
      await loadCart();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not update quantity."
      );
    }
  };

  // Remove product
  const removeItem = async (productId) => {
    try {
      await api.delete(`/cart/items/${productId}`);
      setMessage("Product removed from cart.");
      await loadCart();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not remove product."
      );
    }
  };

  // Clear entire cart
  const clearCart = async () => {
    try {
      await api.delete("/cart");
      setMessage("Cart cleared successfully!");
      await loadCart();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not clear cart."
      );
    }
  };

  if (loading) {
    return <div className="cart-container">Loading cart...</div>;
  }

  return (
    <div className="cart-container">
      <h1>Shopping Cart</h1>

      {message && <p className="cart-message">{message}</p>}

      {cart.items.length === 0 ? (
        <div className="empty-cart">
          <h2>Your cart is empty!</h2>
          <p>Add products to continue shopping.</p>

          <button onClick={() => navigate("/dashboard")}>
            Continue Shopping
          </button>
        </div>
      ) : (
        <>
          <div className="cart-list">
            {cart.items.map((item) => (
              <div className="cart-item" key={item.product_id}>
                <div className="cart-product-info">
                  <h3>{item.product_name}</h3>
                  <p>Price: ₹{Number(item.price).toFixed(2)}</p>
                  <p>
                    Subtotal: ₹
                    {Number(item.subtotal).toFixed(2)}
                  </p>
                </div>

                <div className="quantity-controls">
                  <button
                    onClick={() =>
                      updateQuantity(
                        item.product_id,
                        item.quantity - 1
                      )
                    }
                    disabled={item.quantity <= 1}
                  >
                    -
                  </button>

                  <span>{item.quantity}</span>

                  <button
                    onClick={() =>
                      updateQuantity(
                        item.product_id,
                        item.quantity + 1
                      )
                    }
                  >
                    +
                  </button>
                </div>

                <button
                  className="remove-button"
                  onClick={() => removeItem(item.product_id)}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <h2>Order Summary</h2>

            <p>Total Items: {cart.total_items}</p>

            <h3>
              Total Amount: ₹
              {Number(cart.total_amount).toFixed(2)}
            </h3>

            <button
              className="clear-button"
              onClick={clearCart}
            >
              Clear Cart
            </button>
            <button
              className="checkout-button"
              onClick={() => navigate("/checkout")}
            >
              Proceed to Checkout
            </button>
            <button
              onClick={() => navigate("/dashboard")}
            >
              Continue Shopping
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default Cart;