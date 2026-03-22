import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, useNavigate, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { getCurrentUser, logout } from "./utils/api";

// Protected Route Component
function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    // Verify token is valid
    getCurrentUser()
      .then(() => setIsAuthenticated(true))
      .catch(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("user_id");
        localStorage.removeItem("username");
        setIsAuthenticated(false);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", color: "#fff" }}>Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AppContent() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    if (token && username) {
      setUser(username);
    }
  }, []);

  const handleLogout = () => {
    logout();
    setUser(null);
    navigate("/login");
  };

  const isAuthPage = window.location.pathname === "/login" || window.location.pathname === "/register";

  if (isAuthPage) {
    return <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
    </Routes>;
  }

  return (
    <>
      {/* Top Nav */}
      <nav style={{
        height: 60,
        background: "#0d0d18",
        borderBottom: "1px solid #1e1a33",
        display: "flex",
        alignItems: "center",
        padding: "0 28px",
        gap: "0",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginRight: "40px" }}>
          <div style={{
            width: 32, height: 32, borderRadius: "8px",
            background: "linear-gradient(135deg, #ff4757, #c0392b)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "16px",
          }}>⚠</div>
          <div>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "#fff", letterSpacing: "0.05em" }}>FRAUD SENTINEL</div>
            <div style={{ fontSize: "9px", color: "#5a4f7a", letterSpacing: "0.1em" }}>GROQ + FAISS RAG</div>
          </div>
        </div>

        {/* Nav Links */}
        {[
          { to: "/", label: "📊 Dashboard" },
          { to: "/analyze", label: "🔍 Analyze" },
        ].map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            style={({ isActive }) => ({
              padding: "8px 16px",
              borderRadius: "8px",
              textDecoration: "none",
              fontSize: "12px",
              letterSpacing: "0.05em",
              color: isActive ? "#c084fc" : "#6b5f8a",
              background: isActive ? "#1a1230" : "transparent",
              border: `1px solid ${isActive ? "#7c3aed" : "transparent"}`,
              marginRight: "4px",
              transition: "all 0.15s",
            })}
          >
            {label}
          </NavLink>
        ))}

        <div style={{ marginLeft: "auto", display: "flex", gap: "8px", alignItems: "center" }}>
          <div style={{
            padding: "4px 12px", borderRadius: "20px",
            background: "#0d1a0d", border: "1px solid #1a4a1a",
            fontSize: "11px", color: "#4ade80",
          }}>
            ● API ONLINE
          </div>
          {user && (
            <>
              <div style={{
                padding: "4px 12px", borderRadius: "20px",
                background: "#1a1230", border: "1px solid #7c3aed",
                fontSize: "11px", color: "#c084fc",
              }}>
                👤 {user}
              </div>
              <button
                onClick={handleLogout}
                style={{
                  padding: "4px 12px", borderRadius: "20px",
                  background: "transparent", border: "1px solid #ff4757",
                  fontSize: "11px", color: "#ff4757",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => e.target.style.background = "rgba(255, 71, 87, 0.1)"}
                onMouseLeave={(e) => e.target.style.background = "transparent"}
              >
                Logout
              </button>
            </>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/analyze" element={<ProtectedRoute><Analyze /></ProtectedRoute>} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        minHeight: "100vh",
        background: "#0a0a0f",
        fontFamily: "'DM Mono', 'Courier New', monospace",
        color: "#e8e6f0",
      }}>
        <AppContent />
      </div>
    </BrowserRouter>
  );
}
