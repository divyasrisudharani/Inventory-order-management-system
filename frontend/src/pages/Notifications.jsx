import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Notifications.css";

function Notifications() {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const user = JSON.parse(
    localStorage.getItem("user") || "null"
  );

  const loadNotifications = async () => {
    if (!user?.id) {
      setMessage("User information not found. Please log in again.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);

      const response = await api.get(
        `/notifications/user/${user.id}`
      );

      setNotifications(response.data);

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
        "Unable to load notifications."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const markAsRead = async (notificationId) => {
    try {
      await api.patch(
        `/notifications/${notificationId}/read`
      );

      await loadNotifications();
    } catch (error) {
      setMessage("Unable to mark notification as read.");
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await api.delete(
        `/notifications/${notificationId}`
      );

      setNotifications((previous) =>
        previous.filter((item) => item.id !== notificationId)
      );

      setMessage("Notification deleted successfully.");
    } catch (error) {
      setMessage("Unable to delete notification.");
    }
  };

  if (loading) {
    return <div className="notifications-container">
      Loading notifications...
    </div>;
  }

  return (
    <div className="notifications-container">
      <h1>My Notifications</h1>

      {message && <p>{message}</p>}

      <button onClick={loadNotifications}>
        Refresh
      </button>

      {notifications.length === 0 ? (
        <p>No notifications available.</p>
      ) : (
        notifications.map((notification) => (
          <div
            className="notification-card"
            key={notification.id}
          >
            <h3>{notification.title}</h3>

            <p>{notification.message}</p>

            <p>
              Type: {notification.notification_type}
            </p>

            <p>
              Status: {notification.status}
            </p>

            <p>
              {notification.created_at
                ? new Date(notification.created_at).toLocaleString()
                : ""}
            </p>

            {notification.status !== "READ" && (
              <button
                onClick={() => markAsRead(notification.id)}
              >
                Mark as Read
              </button>
            )}

            <button
              onClick={() => deleteNotification(notification.id)}
            >
              Delete
            </button>
          </div>
        ))
      )}

      <button onClick={() => navigate("/dashboard")}>
        Back to Dashboard
      </button>
    </div>
  );
}

export default Notifications;