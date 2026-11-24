import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./ManageProducts.css";

const emptyForm = {
  name: "",
  description: "",
  category: "",
  brand: "",
  price: "",
  image_url: "",
  rating: 0,
};

function ManageProducts() {
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/products", {
        params: { page: 1, limit: 100 },
      });

      const data = response.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load products."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      brand: form.brand.trim(),
      price: Number(form.price),
      image_url: form.image_url.trim() || null,
      rating: Number(form.rating),
    };

    try {
      setSaving(true);

      if (editingId !== null) {
        await api.put(`/products/${editingId}`, payload);
        setMessage("Product updated successfully!");
      } else {
        await api.post("/products", payload);
        setMessage("Product added successfully!");
      }

      resetForm();
      await loadProducts();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Unable to save product. Please check the entered values."
      );
    } finally {
      setSaving(false);
    }
  };

  const editProduct = (product) => {
    setEditingId(product.id);
    setForm({
      name: product.name || "",
      description: product.description || "",
      category: product.category || "",
      brand: product.brand || "",
      price: product.price ?? "",
      image_url: product.image_url || "",
      rating: product.rating ?? 0,
    });

    setMessage("");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteProduct = async (productId) => {
    const confirmed = window.confirm(
      "Are you sure you want to deactivate this product?"
    );

    if (!confirmed) return;

    setMessage("");
    setError("");

    try {
      await api.delete(`/products/${productId}`);
      setMessage("Product deleted successfully!");
      await loadProducts();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to delete product."
      );
    }
  };

  return (
    <div className="manage-products-container">
      <header className="products-header">
        <div>
          <h1>Manage Products</h1>
          <p>Add, update and manage store products.</p>
        </div>

        <button
          type="button"
          className="back-button"
          onClick={() => navigate("/admin")}
        >
          Back to Admin
        </button>
      </header>

      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}

      <section className="product-form-section">
        <h2>{editingId !== null ? "Edit Product" : "Add New Product"}</h2>

        <form onSubmit={handleSubmit} className="product-form">
          <label>
            Product Name
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              minLength="2"
              maxLength="150"
              required
            />
          </label>

          <label>
            Description
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              minLength="5"
              required
            />
          </label>

          <div className="form-row">
            <label>
              Category
              <input
                name="category"
                value={form.category}
                onChange={handleChange}
                minLength="2"
                maxLength="100"
                required
              />
            </label>

            <label>
              Brand
              <input
                name="brand"
                value={form.brand}
                onChange={handleChange}
                minLength="2"
                maxLength="100"
                required
              />
            </label>
          </div>

          <div className="form-row">
            <label>
              Price (₹)
              <input
                type="number"
                name="price"
                value={form.price}
                onChange={handleChange}
                min="0.01"
                step="0.01"
                required
              />
            </label>

            <label>
              Rating (0–5)
              <input
                type="number"
                name="rating"
                value={form.rating}
                onChange={handleChange}
                min="0"
                max="5"
                step="0.1"
              />
            </label>
          </div>

          <label>
            Image URL (optional)
            <input
              type="url"
              name="image_url"
              value={form.image_url}
              onChange={handleChange}
              placeholder="https://example.com/product.jpg"
            />
          </label>

          <div className="form-buttons">
            <button type="submit" disabled={saving}>
              {saving
                ? "Saving..."
                : editingId !== null
                ? "Update Product"
                : "Add Product"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                className="cancel-edit-button"
                onClick={resetForm}
              >
                Cancel Edit
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="products-list-section">
        <div className="products-list-heading">
          <h2>Product List</h2>
          <button type="button" onClick={loadProducts}>
            Refresh
          </button>
        </div>

        {loading ? (
          <p>Loading products...</p>
        ) : products.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <div className="products-table-wrapper">
            <table className="products-table">
              <thead>
                <tr>
                  <th>Image</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Brand</th>
                  <th>Price</th>
                  <th>Rating</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      {product.image_url ? (
                        <img
                          src={product.image_url}
                          alt={product.name}
                          className="admin-product-image"
                        />
                      ) : (
                        "No image"
                      )}
                    </td>
                    <td>{product.name}</td>
                    <td>{product.category}</td>
                    <td>{product.brand}</td>
                    <td>₹{Number(product.price).toFixed(2)}</td>
                    <td>{product.rating}</td>
                    <td>
                      <button
                        type="button"
                        className="edit-product-button"
                        onClick={() => editProduct(product)}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="delete-product-button"
                        onClick={() => deleteProduct(product.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default ManageProducts;