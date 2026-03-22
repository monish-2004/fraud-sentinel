import { useState, useEffect } from "react";
import { getKnowledgeBase } from "../utils/api";

const FULL_KB = [
  { source: "ATO_Pattern_001", category: "Account Takeover", icon: "🔓",
    summary: "Indicators: new device, password reset, geo-anomaly, unusual time, high-value post-ATO purchase." },
  { source: "CNP_Pattern_002", category: "Card-Not-Present Fraud", icon: "💳",
    summary: "Online fraud indicators: address mismatch, failed CVV attempts, electronics/gift cards, proxy IP." },
  { source: "GEO_Pattern_003", category: "Geo Anomaly", icon: "🌍",
    summary: "Impossible travel detection, overseas IP during domestic use, sanctioned country transactions." },
  { source: "VEL_Pattern_004", category: "Velocity Attack", icon: "⚡",
    summary: "3+ transactions in 10 min, small test amounts before large charge, sequential card testing." },
  { source: "SYN_Pattern_005", category: "Synthetic Identity Fraud", icon: "👤",
    summary: "Real SSN + fake identity, thin credit history, mail-drop addresses, bust-out events." },
  { source: "TOR_Pattern_006", category: "TOR/Proxy Network", icon: "🕵️",
    summary: "Tor exit nodes (185.220.x.x), anonymous proxies, high correlation with crypto/wire fraud." },
  { source: "PHISH_Pattern_007", category: "Phishing / Social Engineering", icon: "🎣",
    summary: "Post-phishing wire transfers, fake bank calls, OTP sharing, P2P platform transactions." },
  { source: "CRYPTO_Pattern_008", category: "Cryptocurrency Fraud", icon: "₿",
    summary: "First-time crypto purchase, foreign exchange, age outliers, irreversible transactions." },
  { source: "SAR_Rules_009", category: "SAR Filing Requirements", icon: "📋",
    summary: "BSA thresholds: $5k suspected illegal, $25k any, structuring, sanctions, terrorism." },
  { source: "SKIM_Pattern_010", category: "Card Skimming", icon: "💾",
    summary: "ATM/gas pump skimmers, clone card usage in different city, magnetic stripe bypass." },
  { source: "FRIENDLY_Pattern_011", category: "Friendly Fraud", icon: "😈",
    summary: "Chargeback abuse, immediate dispute after delivery, digital goods, social media evidence." },
  { source: "ELDER_Pattern_012", category: "Elder Financial Abuse", icon: "👴",
    summary: "Age >65, large withdrawals, wire to unknown, lottery scams, mandatory APS reporting." },
];

export default function KnowledgeBase() {
  const [entries, setEntries] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getKnowledgeBase().then((r) => setEntries(r.entries || [])).catch(() => {});
  }, []);

  const filtered = FULL_KB.filter(
    (e) =>
      e.category.toLowerCase().includes(search.toLowerCase()) ||
      e.source.toLowerCase().includes(search.toLowerCase()) ||
      e.summary.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: "28px 32px", maxWidth: 1200 }}>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ margin: 0, fontSize: "22px", fontWeight: 700, color: "#fff", letterSpacing: "0.02em" }}>
          RAG Knowledge Base
        </h1>
        <p style={{ margin: "6px 0 0", fontSize: "13px", color: "#6b5f8a" }}>
          {FULL_KB.length} fraud pattern documents indexed in FAISS vector store
        </p>
      </div>

      {/* Stats Bar */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
        gap: "12px", marginBottom: "24px",
      }}>
        {[
          { label: "Documents Indexed", value: FULL_KB.length, icon: "📄" },
          { label: "Vector Dimensions", value: "256", icon: "🔢" },
          { label: "Similarity Metric", value: "Cosine (IP)", icon: "📐" },
        ].map((s) => (
          <div key={s.label} style={{
            background: "#111120", border: "1px solid #1e1a33",
            borderRadius: "10px", padding: "14px 18px",
            display: "flex", alignItems: "center", gap: "12px",
          }}>
            <div style={{ fontSize: "24px" }}>{s.icon}</div>
            <div>
              <div style={{ fontSize: "20px", fontWeight: 700, color: "#c084fc" }}>{s.value}</div>
              <div style={{ fontSize: "11px", color: "#5a4f7a" }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Search */}
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="🔍  Search knowledge base..."
        style={{
          width: "100%", marginBottom: "20px", padding: "10px 16px",
          background: "#111120", border: "1px solid #2a1f4a",
          borderRadius: "10px", color: "#e8e6f0", fontSize: "13px",
          fontFamily: "inherit", outline: "none", boxSizing: "border-box",
        }}
      />

      {/* Cards Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "14px" }}>
        {filtered.map((entry) => (
          <div
            key={entry.source}
            onClick={() => setSelected(selected?.source === entry.source ? null : entry)}
            style={{
              background: selected?.source === entry.source ? "#1a1230" : "#111120",
              border: `1px solid ${selected?.source === entry.source ? "#7c3aed" : "#1e1a33"}`,
              borderRadius: "12px", padding: "18px",
              cursor: "pointer", transition: "all 0.15s",
            }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{ fontSize: "24px" }}>{entry.icon}</div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#e8e6f0" }}>{entry.category}</div>
                  <div style={{ fontSize: "10px", color: "#5a4f7a", marginTop: "2px", letterSpacing: "0.05em" }}>{entry.source}</div>
                </div>
              </div>
              <div style={{
                fontSize: "9px", padding: "3px 8px", borderRadius: "10px",
                background: "#7c3aed22", color: "#c084fc", border: "1px solid #7c3aed44",
              }}>INDEXED</div>
            </div>
            <p style={{ fontSize: "12px", color: "#7c6f9e", lineHeight: 1.6, margin: 0 }}>{entry.summary}</p>

            {selected?.source === entry.source && (
              <div style={{
                marginTop: "12px", padding: "12px",
                background: "#0d0d18", borderRadius: "8px",
                border: "1px solid #2a1f4a",
              }}>
                <div style={{ fontSize: "10px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "6px" }}>
                  VECTOR EMBEDDING INFO
                </div>
                <div style={{ fontSize: "11px", color: "#7c6f9e", lineHeight: 1.6 }}>
                  This document is embedded as a 256-dimensional TF-IDF vector in the FAISS IndexFlatIP store.
                  During analysis, cosine similarity is used to retrieve the top-4 most relevant patterns for each transaction query.
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
