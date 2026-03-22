import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../utils/api";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await login(username, password);
      localStorage.setItem("token", response.access_token);
      localStorage.setItem("user_id", response.user_id);
      localStorage.setItem("username", response.username);
      navigate("/");
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      background: "linear-gradient(135deg, #0f0e1a 0%, #1a1829 100%)",
      fontFamily: "Inter, sans-serif",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "400px",
        padding: "40px",
        background: "#111120",
        border: "1px solid #1e1a33",
        borderRadius: "12px",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
      }}>
        <div style={{ marginBottom: "32px", textAlign: "center" }}>
          <h1 style={{
            fontSize: "28px",
            fontWeight: 700,
            color: "#fff",
            margin: "0 0 8px",
            letterSpacing: "0.02em",
          }}>
            Fraud Sentinel
          </h1>
          <p style={{ color: "#6b5f8a", margin: "0", fontSize: "14px" }}>
            Sign in to your account
          </p>
        </div>

        {error && (
          <div style={{
            background: "#ff4757",
            color: "#fff",
            padding: "12px",
            borderRadius: "8px",
            marginBottom: "16px",
            fontSize: "14px",
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label style={{
              display: "block",
              color: "#fff",
              marginBottom: "8px",
              fontSize: "14px",
              fontWeight: 500,
            }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "12px",
                background: "#0f0e1a",
                border: "1px solid #1e1a33",
                borderRadius: "8px",
                color: "#fff",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="Enter your username"
            />
          </div>

          <div style={{ marginBottom: "24px" }}>
            <label style={{
              display: "block",
              color: "#fff",
              marginBottom: "8px",
              fontSize: "14px",
              fontWeight: 500,
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "12px",
                background: "#0f0e1a",
                border: "1px solid #1e1a33",
                borderRadius: "8px",
                color: "#fff",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              background: loading ? "#5a5a6d" : "#7c3aed",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.3s",
            }}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={{ marginTop: "24px", textAlign: "center" }}>
          <p style={{ color: "#6b5f8a", fontSize: "14px", margin: "0" }}>
            Don't have an account?{" "}
            <a href="/register" style={{
              color: "#7c3aed",
              textDecoration: "none",
              fontWeight: 600,
              cursor: "pointer",
            }}>
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
