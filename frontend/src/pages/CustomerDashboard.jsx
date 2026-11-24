import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function CustomerDashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "null");

  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const loadProducts = async () => {
    try {
      const response = await api.get("/products");
      const data = response.data;

      setProducts(
        Array.isArray(data) ? data : data.products || []
      );
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Unable to load products."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const addToCart = async (productId) => {
    try {
      await api.post("/cart/", {
        product_id: productId,
        quantity: 1,
      });
      setMessage("Product added to cart!");
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not add product to cart."
      );
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const filteredProducts = products.filter((product) =>
    product.name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard">
      <header className="navbar">
        <h2>Inventory Store</h2>

        <div>
          <span>Welcome, {user?.full_name}</span>
          <button onClick={() => navigate("/my-orders")}>
            My Orders
          </button>
          <button onClick={() => navigate("/cart")}>
            My Cart
          </button>
          <button onClick={logout}>Logout</button>
          <button onClick={() => navigate("/notifications")}> My Notifications</button>
        </div>
      </header>

      <main className="dashboard-content">
        <h1>Our Products</h1>
        <p>Explore our available products.</p>

        <input
          className="search-input"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {message && <p>{message}</p>}

        {loading ? (
          <p>Loading products...</p>
        ) : filteredProducts.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <div className="product-grid">
            {filteredProducts.map((product) => (
              <div className="product-card" key={product.id}>
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="product-image"
                onError={(e) => {
                 e.currentTarget.style.display = "none";
                }}
              />
            ) : (
              <p>Image not available</p>
            )}
                <h3>{product.name}</h3>
                <p>{product.description}</p>
                <h3>₹{product.price}</h3>

                <button onClick={() => addToCart(product.id)}>
                  Add to Cart
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default CustomerDashboard;