import { useEffect, useState } from "react";
import api from "../services/api";
import "./ManageCustomers.css";

function ManageCustomers() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/auth/admin/customers");

      setCustomers(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load customers. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const filteredCustomers = customers.filter((customer) => {
    const searchValue = search.toLowerCase();

    return (
      customer.full_name?.toLowerCase().includes(searchValue) ||
      customer.email?.toLowerCase().includes(searchValue) ||
      String(customer.id).includes(searchValue)
    );
  });

  const activeCustomers = customers.filter(
    (customer) => customer.is_active
  ).length;

  const inactiveCustomers = customers.length - activeCustomers;

  const formatDate = (date) => {
    if (!date) return "N/A";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return "N/A";
    }

    return parsedDate.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="manage-customers-page">
        <p className="customers-message">Loading customers...</p>
      </div>
    );
  }

  return (
    <div className="manage-customers-page">
      <div className="customers-header">
        <div>
          <h1>Manage Customers</h1>
          <p>View and monitor registered customers</p>
        </div>

        <button
          className="customers-refresh-btn"
          onClick={fetchCustomers}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="customers-summary">
        <div className="customer-summary-card">
          <span>Total Customers</span>
          <h2>{customers.length}</h2>
        </div>

        <div className="customer-summary-card">
          <span>Active Customers</span>
          <h2>{activeCustomers}</h2>
        </div>

        <div className="customer-summary-card">
          <span>Inactive Customers</span>
          <h2>{inactiveCustomers}</h2>
        </div>
      </div>

      {error && (
        <div className="customers-error">
          {error}
          <button onClick={fetchCustomers}>Retry</button>
        </div>
      )}

      {!error && (
        <>
          <div className="customers-toolbar">
            <input
              type="text"
              placeholder="Search by customer name, email or ID..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />

            <span>
              Showing {filteredCustomers.length} of {customers.length}
            </span>
          </div>

          {filteredCustomers.length === 0 ? (
            <div className="customers-empty">
              <h3>No Customers Found</h3>
              <p>
                {search
                  ? "Try another search term."
                  : "Registered customers will appear here."}
              </p>
            </div>
          ) : (
            <div className="customers-table-container">
              <table className="customers-table">
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Full Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Account Status</th>
                    <th>Registered Date</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredCustomers.map((customer) => (
                    <tr key={customer.id}>
                      <td>#{customer.id}</td>

                      <td className="customer-name">
                        {customer.full_name}
                      </td>

                      <td>{customer.email}</td>

                      <td>
                        <span className="customer-role">
                          {customer.role}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`customer-status ${
                            customer.is_active ? "active" : "inactive"
                          }`}
                        >
                          {customer.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>

                      <td>{formatDate(customer.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default ManageCustomers;