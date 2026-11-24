import { useEffect, useState } from "react";
import api from "../services/api";
import "./ManageInventory.css";

function ManageInventory() {
  const [inventory, setInventory] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showAddForm, setShowAddForm] = useState(false);
  const [showStockForm, setShowStockForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState("");

  const [newInventory, setNewInventory] = useState({
    product_id: "",
    quantity: 0,
    low_stock_threshold: 5,
  });

  const [stockData, setStockData] = useState({
    product_id: "",
    quantity: "",
    action: "STOCK_IN",
    reason: "",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const [inventoryResponse, productResponse] = await Promise.all([
        api.get("/inventory", {
          params: { skip: 0, limit: 100 },
        }),
        api.get("/products", {
          params: { page: 1, limit: 100 },
        }),
      ]);

      const inventoryData = Array.isArray(inventoryResponse.data)
        ? inventoryResponse.data
        : inventoryResponse.data.items || [];

      const productData = Array.isArray(productResponse.data)
        ? productResponse.data
        : productResponse.data.items || [];

      setInventory(inventoryData);
      setProducts(productData);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load inventory data."
      );
    } finally {
      setLoading(false);
    }
  };

  const getProduct = (productId) => {
    return products.find(
      (product) => product.id === Number(productId)
    );
  };

  const getAvailableStock = (item) => {
    return item.quantity - item.reserved_quantity;
  };

  const isLowStock = (item) => {
    return getAvailableStock(item) <= item.low_stock_threshold;
  };

  const handleAddInventory = async (e) => {
    e.preventDefault();

    try {
      setError("");
      setSuccess("");

      await api.post("/inventory", {
        product_id: Number(newInventory.product_id),
        quantity: Number(newInventory.quantity),
        low_stock_threshold: Number(
          newInventory.low_stock_threshold
        ),
      });

      setSuccess("Inventory created successfully.");

      setNewInventory({
        product_id: "",
        quantity: 0,
        low_stock_threshold: 5,
      });

      setShowAddForm(false);
      await fetchData();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to create inventory."
      );
    }
  };

  const openStockForm = (item) => {
    setSelectedProduct(item.product_id);

    setStockData({
      product_id: item.product_id,
      quantity: "",
      action: "STOCK_IN",
      reason: "",
    });

    setShowStockForm(true);
    setError("");
    setSuccess("");
  };

  const handleStockAdjustment = async (e) => {
    e.preventDefault();

    const amount = Number(stockData.quantity);

    if (!amount || amount <= 0) {
      setError("Please enter a quantity greater than zero.");
      return;
    }

    if (!stockData.reason.trim()) {
      setError("Please enter a reason for the stock adjustment.");
      return;
    }

    const quantityChange =
      stockData.action === "STOCK_IN" ? amount : -amount;

    try {
      setError("");
      setSuccess("");

      await api.patch(
        `/inventory/${selectedProduct}/stock`,
        {
          quantity_change: quantityChange,
          transaction_type: stockData.action,
          reason: stockData.reason,
        }
      );

      setSuccess("Stock updated successfully.");
      setShowStockForm(false);

      await fetchData();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to update stock."
      );
    }
  };

  const productsWithoutInventory = products.filter(
    (product) =>
      !inventory.some(
        (item) => item.product_id === product.id
      )
  );

  const totalItems = inventory.length;

  const totalStock = inventory.reduce(
    (sum, item) => sum + item.quantity,
    0
  );

  const totalReserved = inventory.reduce(
    (sum, item) => sum + item.reserved_quantity,
    0
  );

  const lowStockCount = inventory.filter(isLowStock).length;

  return (
    <div className="inventory-page">
      <div className="inventory-header">
        <div>
          <h1>Manage Inventory</h1>
          <p>Monitor and manage your product stock.</p>
        </div>

        <button
          className="inventory-add-btn"
          onClick={() => {
            setShowAddForm(!showAddForm);
            setShowStockForm(false);
            setError("");
            setSuccess("");
          }}
        >
          + Add Inventory
        </button>
      </div>

      {error && <div className="inventory-alert error">{error}</div>}
      {success && (
        <div className="inventory-alert success">{success}</div>
      )}

      <div className="inventory-stats">
        <div className="inventory-stat-card">
          <span>Total Products</span>
          <h2>{totalItems}</h2>
        </div>

        <div className="inventory-stat-card">
          <span>Total Stock</span>
          <h2>{totalStock}</h2>
        </div>

        <div className="inventory-stat-card">
          <span>Reserved Stock</span>
          <h2>{totalReserved}</h2>
        </div>

        <div className="inventory-stat-card low-stock-card">
          <span>Low Stock Products</span>
          <h2>{lowStockCount}</h2>
        </div>
      </div>

      {showAddForm && (
        <form
          className="inventory-form"
          onSubmit={handleAddInventory}
        >
          <h2>Add Product Inventory</h2>

          <label>Select Product</label>
          <select
            value={newInventory.product_id}
            onChange={(e) =>
              setNewInventory({
                ...newInventory,
                product_id: e.target.value,
              })
            }
            required
          >
            <option value="">Choose a product</option>

            {productsWithoutInventory.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} (ID: {product.id})
              </option>
            ))}
          </select>

          <label>Initial Quantity</label>
          <input
            type="number"
            min="0"
            value={newInventory.quantity}
            onChange={(e) =>
              setNewInventory({
                ...newInventory,
                quantity: e.target.value,
              })
            }
            required
          />

          <label>Low Stock Threshold</label>
          <input
            type="number"
            min="0"
            value={newInventory.low_stock_threshold}
            onChange={(e) =>
              setNewInventory({
                ...newInventory,
                low_stock_threshold: e.target.value,
              })
            }
            required
          />

          <div className="inventory-form-actions">
            <button type="submit" className="inventory-save-btn">
              Create Inventory
            </button>

            <button
              type="button"
              className="inventory-cancel-btn"
              onClick={() => setShowAddForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {showStockForm && (
        <form
          className="inventory-form"
          onSubmit={handleStockAdjustment}
        >
          <h2>Update Stock</h2>

          <p>
            Product:{" "}
            <strong>
              {getProduct(selectedProduct)?.name ||
                `Product ID ${selectedProduct}`}
            </strong>
          </p>

          <label>Stock Action</label>
          <select
            value={stockData.action}
            onChange={(e) =>
              setStockData({
                ...stockData,
                action: e.target.value,
              })
            }
          >
            <option value="STOCK_IN">Stock In (Increase)</option>
            <option value="STOCK_OUT">Stock Out (Decrease)</option>
          </select>

          <label>Quantity</label>
          <input
            type="number"
            min="1"
            value={stockData.quantity}
            onChange={(e) =>
              setStockData({
                ...stockData,
                quantity: e.target.value,
              })
            }
            placeholder="Enter quantity"
            required
          />

          <label>Reason</label>
          <input
            type="text"
            value={stockData.reason}
            onChange={(e) =>
              setStockData({
                ...stockData,
                reason: e.target.value,
              })
            }
            placeholder="Example: New stock received"
            required
          />

          <div className="inventory-form-actions">
            <button type="submit" className="inventory-save-btn">
              Update Stock
            </button>

            <button
              type="button"
              className="inventory-cancel-btn"
              onClick={() => setShowStockForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="inventory-table-container">
        <div className="inventory-table-header">
          <h2>Inventory Details</h2>

          <button
            className="inventory-refresh-btn"
            onClick={fetchData}
          >
            ↻ Refresh
          </button>
        </div>

        {loading ? (
          <p className="inventory-message">Loading inventory...</p>
        ) : inventory.length === 0 ? (
          <p className="inventory-message">
            No inventory records found. Add inventory to get started.
          </p>
        ) : (
          <div className="inventory-table-scroll">
            <table className="inventory-table">
              <thead>
                <tr>
                  <th>Product ID</th>
                  <th>Product Name</th>
                  <th>Total Quantity</th>
                  <th>Reserved</th>
                  <th>Available</th>
                  <th>Low Stock Limit</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {inventory.map((item) => {
                  const product = getProduct(item.product_id);
                  const available = getAvailableStock(item);

                  return (
                    <tr key={item.id}>
                      <td>{item.product_id}</td>
                      <td>
                        {product?.name || "Unknown Product"}
                      </td>
                      <td>{item.quantity}</td>
                      <td>{item.reserved_quantity}</td>
                      <td>{available}</td>
                      <td>{item.low_stock_threshold}</td>

                      <td>
                        <span
                          className={
                            isLowStock(item)
                              ? "inventory-status low"
                              : "inventory-status available"
                          }
                        >
                          {isLowStock(item)
                            ? "Low Stock"
                            : "Available"}
                        </span>
                      </td>

                      <td>
                        <button
                          className="inventory-update-btn"
                          onClick={() => openStockForm(item)}
                        >
                          Update Stock
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ManageInventory;