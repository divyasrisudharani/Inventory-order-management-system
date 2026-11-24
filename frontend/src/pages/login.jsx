import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";

function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setLoading(true);

    try {
     const response = await api.post("/auth/login", {
          email, password,
     });

     localStorage.setItem("access_token",
     response.data.access_token);
     localStorage.setItem("refresh_token",
     response.data.refresh_token);

     const userResponse = await api.get("/auth/me");
     const user = userResponse.data;

     localStorage.setItem("user", JSON.stringify(user));

     if (user.role === "administrator") {
          navigate("/admin");
     } else if (user.role === "customer") {
         navigate("/dashboard");
     } else {
       setMessage("Unauthorized user role.");
       localStorage.clear();
} catch (error) {
      setMessage(
        error.response?.data?.detail || "Login failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Welcome Back</h2>
        <p>Login to your account</p>

        <input
          name="email"
          type="email"
          placeholder="Email Address"
          value={form.email}
          onChange={handleChange}
          required
        />

        <input
          name="password"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>

        {message && <p>{message}</p>}

        <p>
          New user? <Link to="/register">Create Account</Link>
        </p>
      </form>
    </div>
  );
}

export default Login;