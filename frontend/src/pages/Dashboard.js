import { useState, useEffect } from "react";
import { getDashboardStats } from "../utils/api";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial load
    getDashboardStats().then(setStats).finally(() => setLoading(false));

    // Auto-refresh every 3 seconds to pick up new analyzed transactions
    const interval = setInterval(() => {
      getDashboardStats().then(setStats);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingState />;

  return (
    <div style={{ padding: "28px 32px", maxWidth: 1400 }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700, color: "#fff", letterSpacing: "0.02em" }}>
          Fraud Operations Dashboard
        </h1>
        <p style={{ margin: "6px 0 0", fontSize: "13px", color: "#6b5f8a" }}>
          Real-time fraud detection powered by Groq LLM + FAISS RAG
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
        {[
          { label: "Total Analyzed", value: stats.total_analyzed.toLocaleString(), icon: "🔍", color: "#7c3aed", sub: "All time" },
          { label: "Flagged Today", value: stats.flagged_today, icon: "⚠️", color: "#ffa502", sub: "+3 from yesterday" },
          { label: "High Risk", value: stats.high_risk, icon: "🔴", color: "#ff4757", sub: "Requires review" },
          { label: "SAR Pending", value: stats.sar_pending, icon: "📋", color: "#ff6b35", sub: "File within 30 days" },
        ].map((kpi) => (
          <div key={kpi.label} style={{
            background: "#111120", border: "1px solid #1e1a33",
            borderRadius: "12px", padding: "20px",
            borderTop: `3px solid ${kpi.color}`,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontSize: "11px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "8px" }}>
                  {kpi.label.toUpperCase()}
                </div>
                <div style={{ fontSize: "32px", fontWeight: 700, color: "#fff", lineHeight: 1 }}>
                  {kpi.value}
                </div>
                <div style={{ fontSize: "11px", color: "#5a4f7a", marginTop: "6px" }}>{kpi.sub}</div>
              </div>
              <div style={{ fontSize: "28px" }}>{kpi.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "16px", marginBottom: "24px" }}>
        {/* Area Chart */}
        <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "16px" }}>
            WEEKLY TRANSACTION VOLUME
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={stats.weekly_data}>
              <defs>
                <linearGradient id="flagGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff4757" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff4757" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="clearGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e1a33" strokeDasharray="3 3" />
              <XAxis dataKey="day" stroke="#3a2f5a" tick={{ fill: "#7c6f9e", fontSize: 11 }} />
              <YAxis stroke="#3a2f5a" tick={{ fill: "#7c6f9e", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: "#0d0d18", border: "1px solid #2a1f4a", borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: "#c084fc" }}
              />
              <Area type="monotone" dataKey="cleared" stroke="#7c3aed" fill="url(#clearGrad)" strokeWidth={2} name="Cleared" />
              <Area type="monotone" dataKey="flagged" stroke="#ff4757" fill="url(#flagGrad)" strokeWidth={2} name="Flagged" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "16px" }}>
            RISK DISTRIBUTION
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={stats.risk_distribution} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="count" nameKey="level">
                {stats.risk_distribution.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#0d0d18", border: "1px solid #2a1f4a", borderRadius: 8, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {stats.risk_distribution.map((r, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: r.color }} />
                  <span style={{ fontSize: "11px", color: "#7c6f9e" }}>{r.level}</span>
                </div>
                <span style={{ fontSize: "11px", color: "#c084fc", fontWeight: 600 }}>{r.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        {/* Top Patterns Bar Chart */}
        <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "16px" }}>
            TOP FRAUD PATTERNS
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={stats.fraud_patterns} layout="vertical">
              <CartesianGrid stroke="#1e1a33" strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" stroke="#3a2f5a" tick={{ fill: "#7c6f9e", fontSize: 11 }} />
              <YAxis type="category" dataKey="pattern" stroke="#3a2f5a" tick={{ fill: "#7c6f9e", fontSize: 10 }} width={120} />
              <Tooltip contentStyle={{ background: "#0d0d18", border: "1px solid #2a1f4a", borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" fill="#7c3aed" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Alerts */}
        <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "20px" }}>
          <div style={{ fontSize: "12px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "16px" }}>
            RECENT ALERTS
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {stats.recent_alerts.map((alert) => (
              <div key={alert.id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 12px", background: "#0d0d18",
                borderRadius: "8px", border: "1px solid #1e1a33",
              }}>
                <div>
                  <div style={{ fontSize: "12px", color: "#c084fc", fontWeight: 600 }}>{alert.id}</div>
                  <div style={{ fontSize: "11px", color: "#7c6f9e", marginTop: "2px" }}>{alert.pattern}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{
                    fontSize: "12px", fontWeight: 700,
                    color: alert.risk >= 80 ? "#ff4757" : alert.risk >= 60 ? "#ff6b35" : "#ffa502",
                  }}>
                    Risk: {alert.risk}
                  </div>
                  <div style={{ fontSize: "11px", color: "#5a4f7a", marginTop: "2px" }}>${alert.amount.toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "60vh" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: "40px", marginBottom: "16px" }}>⏳</div>
        <div style={{ color: "#7c6f9e", fontSize: "13px", letterSpacing: "0.1em" }}>LOADING DASHBOARD...</div>
      </div>
    </div>
  );
}
