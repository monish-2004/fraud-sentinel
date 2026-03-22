import { useState } from "react";
import { analyzeTransaction, analyzeText, generateTransactions, uploadPDF, exportReportToPDF } from "../utils/api";
import Chat from "../components/Chat";

const FLAG_COLORS = {
  "geo-anomaly": "#ff6b6b", "unusual-hour": "#ffa94d",
  "new-device": "#f06595", "high-value": "#cc5de8",
  "velocity-spike": "#ff6b6b", "repeated-failure": "#ffa94d",
  "tor-node": "#ff4757", "crypto-merchant": "#f06595",
};

const getRiskColor = (score) => {
  if (score >= 80) return "#ff4757";
  if (score >= 60) return "#ff6b35";
  if (score >= 40) return "#ffa502";
  return "#2ed573";
};

export default function Analyze() {
  const [mode, setMode] = useState("structured"); // structured | text | pdf
  const [transactions, setTransactions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState("explanation");
  const [customText, setCustomText] = useState("");
  const [genCount, setGenCount] = useState(5);
  const [ragSources, setRagSources] = useState([]);
  const [pdfReport, setPdfReport] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateTransactions(genCount, true);
      setTransactions(res.transactions);
      setSelected(null);
      setAnalysis(null);
    } catch (e) {
      alert("Generation failed: " + e.message);
    }
    setGenerating(false);
  };

  const handleAnalyze = async (tx) => {
    setSelected(tx);
    setAnalysis(null);
    setRagSources([]);
    setLoading(true);
    setActiveTab("explanation");
    try {
      const res = await analyzeTransaction(tx);
      setAnalysis(res.analysis);
      setRagSources(res.rag_sources || []);
    } catch (e) {
      setAnalysis({ error: "Analysis failed: " + e.message });
    }
    setLoading(false);
  };

  const handleTextAnalyze = async () => {
    if (!customText.trim()) return;
    setAnalysis(null);
    setRagSources([]);
    setLoading(true);
    setActiveTab("explanation");
    try {
      const res = await analyzeText(customText);
      setAnalysis(res.analysis);
      setRagSources(res.rag_sources || []);
    } catch (e) {
      setAnalysis({ error: "Analysis failed: " + e.message });
    }
    setLoading(false);
  };

  const handlePdfUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const res = await uploadPDF(file);
      setPdfReport(res.report);
      setSelected(null);
      setAnalysis(null);
    } catch (error) {
      alert("PDF upload failed: " + error.message);
    }
    setUploading(false);
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)" }}>
      {/* Left Panel */}
      <div style={{
        width: "360px", minWidth: "360px",
        background: "#0d0d18", borderRight: "1px solid #1e1a33",
        display: "flex", flexDirection: "column", overflow: "hidden",
      }}>
        {/* Mode Switcher */}
        <div style={{ padding: "16px", borderBottom: "1px solid #1e1a33" }}>
          <div style={{ display: "flex", gap: "6px", marginBottom: "12px" }}>
            {["structured", "text", "pdf"].map((m) => (
              <button key={m} onClick={() => { setMode(m); setPdfReport(null); setTransactions([]); }} style={{
                flex: 1, padding: "7px", borderRadius: "7px",
                border: "1px solid", borderColor: mode === m ? "#7c3aed" : "#1e1a33",
                background: mode === m ? "#1a1230" : "transparent",
                color: mode === m ? "#c084fc" : "#5a4f7a",
                cursor: "pointer", fontSize: "11px", letterSpacing: "0.08em",
                fontFamily: "inherit", textTransform: "uppercase",
              }}>
                {m === "structured" ? "📊 LLM Generated" : m === "text" ? "✏️ Custom Text" : "📄 PDF Upload"}
              </button>
            ))}
          </div>

          {mode === "structured" ? (
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <select
                value={genCount}
                onChange={(e) => setGenCount(Number(e.target.value))}
                style={{
                  flex: 1, padding: "7px 10px", background: "#111120",
                  border: "1px solid #2a1f4a", borderRadius: "7px",
                  color: "#c084fc", fontSize: "12px", fontFamily: "inherit", outline: "none",
                }}>
                {[3, 5, 8, 10].map((n) => <option key={n} value={n}>{n} transactions</option>)}
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating}
                style={{
                  padding: "7px 16px", borderRadius: "7px",
                  background: generating ? "#2a1f4a" : "linear-gradient(135deg, #7c3aed, #a855f7)",
                  border: "none", color: "#fff", cursor: "pointer",
                  fontSize: "11px", fontFamily: "inherit", fontWeight: 600, letterSpacing: "0.05em",
                }}>
                {generating ? "⏳" : "⚡ Generate"}
              </button>
            </div>
          ) : mode === "text" ? (
            <div>
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="Describe the suspicious transaction..."
                style={{
                  width: "100%", height: "80px", background: "#111120",
                  border: "1px solid #2a1f4a", borderRadius: "7px",
                  padding: "8px 10px", color: "#e8e6f0", fontSize: "12px",
                  fontFamily: "inherit", resize: "none", outline: "none",
                  lineHeight: 1.5, boxSizing: "border-box",
                }}
              />
              <button
                onClick={handleTextAnalyze}
                disabled={loading || !customText.trim()}
                style={{
                  marginTop: "8px", width: "100%", padding: "8px",
                  background: "linear-gradient(135deg, #7c3aed, #a855f7)",
                  border: "none", borderRadius: "7px", color: "#fff",
                  cursor: "pointer", fontSize: "11px", fontFamily: "inherit",
                  fontWeight: 600, letterSpacing: "0.08em",
                }}>
                ⚡ ANALYZE WITH RAG
              </button>
            </div>
          ) : (
            <div>
              <label style={{
                display: "flex", flexDirection: "column", alignItems: "center", gap: "8px",
                padding: "20px 16px", background: "#111120", border: "2px dashed #2a1f4a",
                borderRadius: "8px", cursor: uploading ? "not-allowed" : "pointer",
                opacity: uploading ? 0.6 : 1,
              }}>
                <span style={{ fontSize: "24px" }}>📤</span>
                <span style={{ fontSize: "11px", color: "#c084fc", fontWeight: 600, textAlign: "center" }}>
                  {uploading ? "UPLOADING..." : "Click to upload PDF"}
                </span>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handlePdfUpload}
                  disabled={uploading}
                  style={{ display: "none" }}
                />
              </label>
              <div style={{ fontSize: "11px", color: "#5a4f7a", marginTop: "8px", textAlign: "center" }}>
                PDF should contain transaction details with columns like: Date, Merchant, Amount, Location, etc.
              </div>
            </div>
          )}
        </div>

        {/* Transaction List or PDF Report Summary */}
        <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
          {mode === "pdf" && pdfReport ? (
            <PDFReportSummary report={pdfReport} />
          ) : mode === "structured" && transactions.length === 0 && !uploading ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "#3a2f5a" }}>
              <div style={{ fontSize: "32px", marginBottom: "12px" }}>🤖</div>
              <div style={{ fontSize: "12px", letterSpacing: "0.1em" }}>
                Click Generate to create LLM-synthesized transactions
              </div>
            </div>
          ) : mode !== "structured" && !uploading ? null : (
            transactions.map((tx, i) => (
              <div
                key={tx.transaction_id}
                onClick={() => handleAnalyze(tx)}
                style={{
                  background: selected?.transaction_id === tx.transaction_id ? "#1a1230" : "#111120",
                  border: `1px solid ${selected?.transaction_id === tx.transaction_id ? "#7c3aed" : "#1e1a33"}`,
                  borderRadius: "10px", padding: "12px", marginBottom: "8px",
                  cursor: "pointer", transition: "all 0.15s",
                }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "11px", color: "#c084fc", fontWeight: 600 }}>{tx.transaction_id}</span>
                  <span style={{ fontSize: "13px", fontWeight: 700, color: tx.is_suspicious ? "#ff4757" : "#2ed573" }}>
                    ${Number(tx.amount).toFixed(2)}
                  </span>
                </div>
                <div style={{ fontSize: "12px", color: "#a89bc2", marginBottom: "4px" }}>{tx.merchant}</div>
                <div style={{ fontSize: "11px", color: "#5a4f7a", marginBottom: "8px" }}>
                  📍 {tx.location} · {tx.time}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "3px", alignItems: "center" }}>
                  {tx.is_suspicious && (
                    <span style={{
                      fontSize: "9px", padding: "2px 6px", borderRadius: "10px",
                      background: "#ff475718", color: "#ff4757",
                      border: "1px solid #ff475740", fontWeight: 600,
                    }}>SUSPICIOUS</span>
                  )}
                  {(tx.flags || []).slice(0, 3).map((f) => (
                    <span key={f} style={{
                      fontSize: "9px", padding: "2px 6px", borderRadius: "10px",
                      background: (FLAG_COLORS[f] || "#888") + "22",
                      color: FLAG_COLORS[f] || "#888",
                      border: `1px solid ${(FLAG_COLORS[f] || "#888")}44`,
                    }}>{f}</span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right Panel - Analysis or PDF Report */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 28px" }}>
        {mode === "pdf" && pdfReport ? (
          <PDFReportView report={pdfReport} />
        ) : loading ? (
          <AnalysisLoader />
        ) : !analysis ? (
          <EmptyState mode={mode} />
        ) : analysis.error ? (
          <div style={{ color: "#ff6b6b", padding: "20px" }}>{analysis.error}</div>
        ) : (
          <AnalysisView
            analysis={analysis}
            transaction={selected}
            ragSources={ragSources}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />
        )}
      </div>
    </div>
  );
}

function PDFReportSummary({ report }) {
  const { statistics } = report;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{
        background: "#111120", border: "1px solid #1e1a33",
        borderRadius: "10px", padding: "12px",
      }}>
        <div style={{ fontSize: "10px", color: "#5a4f7a", marginBottom: "4px" }}>📊 TRANSACTIONS</div>
        <div style={{ fontSize: "18px", fontWeight: 700, color: "#c084fc" }}>
          {statistics.total_transactions}
        </div>
        <div style={{ fontSize: "11px", color: "#7c6f9e" }}>Total: ${Number(statistics.total_amount).toFixed(2)}</div>
      </div>

      <div style={{
        background: "#111120", border: "1px solid #1e1a33",
        borderRadius: "10px", padding: "12px",
      }}>
        <div style={{ fontSize: "10px", color: "#5a4f7a", marginBottom: "4px" }}>🚨 FRAUD DETECTED</div>
        <div style={{ fontSize: "18px", fontWeight: 700, color: "#ff4757" }}>
          {statistics.fraud_detected_count}
        </div>
        <div style={{ fontSize: "11px", color: "#7c6f9e" }}>{statistics.fraud_detection_rate}</div>
      </div>

      <div style={{
        background: "#111120", border: "1px solid #1e1a33",
        borderRadius: "10px", padding: "12px",
      }}>
        <div style={{ fontSize: "10px", color: "#5a4f7a", marginBottom: "4px" }}>⚠️ HIGH RISK</div>
        <div style={{ fontSize: "18px", fontWeight: 700, color: "#ff6b35" }}>
          {statistics.high_risk_count}
        </div>
        <div style={{ fontSize: "11px", color: "#7c6f9e" }}>Requires action</div>
      </div>

      <div style={{
        background: "#111120", border: "1px solid #1e1a33",
        borderRadius: "10px", padding: "12px",
      }}>
        <div style={{ fontSize: "10px", color: "#5a4f7a", marginBottom: "4px" }}>🔴 CRITICAL</div>
        <div style={{ fontSize: "18px", fontWeight: 700, color: "#cc5de8" }}>
          {statistics.critical_count}
        </div>
        <div style={{ fontSize: "11px", color: "#7c6f9e" }}>Immediate action</div>
      </div>
    </div>
  );
}

function PDFReportView({ report }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [exporting, setExporting] = useState(false);

  const handleExportPDF = async () => {
    try {
      setExporting(true);
      const pdfBlob = await exportReportToPDF(report.reportId);
      
      // Create download link
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `fraud_report_${report.reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert("Failed to export PDF: " + error.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      {/* Header with Export Button */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div style={{ display: "flex", gap: "4px", overflowX: "auto", flex: 1 }}>
          {["overview", "patterns", "risks", "actions", "findings"].map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              padding: "8px 16px", borderRadius: "8px", border: "1px solid",
              borderColor: activeTab === tab ? "#7c3aed" : "#1e1a33",
              background: activeTab === tab ? "#1a1230" : "transparent",
              color: activeTab === tab ? "#c084fc" : "#5a4f7a",
              cursor: "pointer", fontSize: "11px", letterSpacing: "0.08em",
              fontFamily: "inherit", textTransform: "uppercase", whiteSpace: "nowrap",
            }}>
              {tab}
            </button>
          ))}
        </div>
        <button
          onClick={handleExportPDF}
          disabled={exporting}
          style={{
            marginLeft: "12px", padding: "8px 16px", borderRadius: "8px",
            background: exporting ? "#2a1f4a" : "linear-gradient(135deg, #ff4757, #ff6b35)",
            border: "none", color: "#fff", cursor: "pointer",
            fontSize: "11px", fontFamily: "inherit", fontWeight: 600,
            letterSpacing: "0.08em", whiteSpace: "nowrap", flexShrink: 0,
          }}>
          {exporting ? "⏳ EXPORTING..." : "📥 EXPORT PDF"}
        </button>
      </div>

      {activeTab === "overview" && (
        <div>
          <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "20px", marginBottom: "20px" }}>
            <Label>REPORT SUMMARY</Label>
            <p style={{ fontSize: "13px", color: "#d4cfe8", lineHeight: 1.8, margin: 0 }}>
              {report.summary}
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
            <StatBox label="Total Transactions" value={report.statistics.total_transactions} color="#c084fc" />
            <StatBox label="Total Amount" value={`$${Number(report.statistics.total_amount).toFixed(2)}`} color="#c084fc" />
            <StatBox label="Fraud Detected" value={report.statistics.fraud_detected_count} color="#ff4757" highlight />
            <StatBox label="Detection Rate" value={report.statistics.fraud_detection_rate} color="#ff6b35" highlight />
            <StatBox label="High Risk" value={report.statistics.high_risk_count} color="#ff6b35" />
            <StatBox label="Critical" value={report.statistics.critical_count} color="#cc5de8" />
          </div>
        </div>
      )}

      {activeTab === "patterns" && (
        <div>
          <Label>FRAUD PATTERNS DETECTED</Label>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {report.fraudReasons.map((reason, i) => (
              <div key={i} style={{
                background: "#111120", border: "1px solid #1e1a33", borderRadius: "10px",
                padding: "14px", borderLeft: "3px solid #7c3aed",
              }}>
                <div style={{ fontSize: "12px", color: "#c084fc", fontWeight: 600 }}>
                  {reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "risks" && (
        <div>
          {report.riskySummary.merchants.length > 0 && (
            <div style={{ marginBottom: "20px" }}>
              <Label>RISKY MERCHANTS</Label>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {report.riskySummary.merchants.map((m, i) => (
                  <RiskBox key={i} item={m} type="merchant" />
                ))}
              </div>
            </div>
          )}

          {report.riskySummary.locations.length > 0 && (
            <div>
              <Label>RISKY LOCATIONS</Label>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {report.riskySummary.locations.map((l, i) => (
                  <RiskBox key={i} item={l} type="location" />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "actions" && (
        <div>
          <Label>RECOMMENDED NEXT STEPS</Label>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {report.recommendedActions.map((action, i) => (
              <div key={i} style={{
                display: "flex", gap: "12px", alignItems: "flex-start",
                background: "#111120", border: "1px solid #1e1a33", borderRadius: "10px",
                padding: "14px",
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
                  background: `hsl(${270 - i * 25}, 60%, 40%)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "11px", fontWeight: 700, color: "#fff",
                }}>{i + 1}</div>
                <div style={{ fontSize: "12px", color: "#d4cfe8", lineHeight: 1.6 }}>
                  {action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "findings" && (
        <div>
          <Label>DETAILED FINDINGS - HIGH RISK TRANSACTIONS</Label>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {report.detailedFindings.map((finding, i) => (
              <div key={i} style={{
                background: "#111120", border: "1px solid #1e1a33", borderRadius: "10px",
                padding: "14px", borderLeft: `3px solid ${getRiskColor(finding.risk_score)}`,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <div style={{ fontSize: "12px", color: "#c084fc", fontWeight: 600 }}>
                    {finding.transaction_id}
                  </div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: getRiskColor(finding.risk_score) }}>
                    {finding.risk_score}%
                  </div>
                </div>
                <div style={{ fontSize: "12px", color: "#a89bc2", marginBottom: "6px" }}>
                  {finding.merchant} · ${Number(finding.amount).toFixed(2)} · {finding.location}
                </div>
                <div style={{ fontSize: "11px", color: "#7c6f9e", marginBottom: "6px" }}>
                  <strong>Pattern:</strong> {finding.fraud_pattern}
                </div>
                <div style={{ fontSize: "12px", color: "#d4cfe8", lineHeight: 1.6 }}>
                  {finding.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value, color, highlight }) {
  return (
    <div style={{
      background: "#111120", border: `1px solid ${highlight ? "#2a1f4a" : "#1e1a33"}`,
      borderRadius: "10px", padding: "14px",
    }}>
      <div style={{ fontSize: "10px", color: "#5a4f7a", marginBottom: "6px", letterSpacing: "0.1em" }}>
        {label}
      </div>
      <div style={{ fontSize: "20px", fontWeight: 700, color }}>
        {value}
      </div>
    </div>
  );
}

function RiskBox({ item, type }) {
  const key = type === "merchant" ? "merchant" : "location";
  return (
    <div style={{
      background: "#111120", border: "1px solid #1e1a33", borderRadius: "10px",
      padding: "14px", borderLeft: `3px solid ${getRiskColor(item.max_risk_score)}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
        <div style={{ fontSize: "12px", color: "#c084fc", fontWeight: 600 }}>
          {item[key]}
        </div>
        <div style={{ fontSize: "13px", fontWeight: 700, color: getRiskColor(item.max_risk_score) }}>
          {item.max_risk_score}%
        </div>
      </div>
      <div style={{ fontSize: "11px", color: "#7c6f9e" }}>
        {item.fraud_count} fraud · ${Number(item.total_amount).toFixed(2)}
      </div>
    </div>
  );
}

function Label({ children }) {
  return (
    <div style={{ fontSize: "10px", color: "#5a4f7a", letterSpacing: "0.12em", marginBottom: "12px", fontWeight: 600 }}>
      {children}
    </div>
  );
}

function AnalysisView({ analysis, transaction, ragSources, activeTab, setActiveTab }) {
  const score = analysis.risk_score || 0;
  const color = getRiskColor(score);
  const circ = 2 * Math.PI * 52;
  const offset = circ - (score / 100) * circ;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "20px", height: "100%" }}>
      {/* Left: Analysis Details */}
      <div style={{ overflowY: "auto", paddingRight: "4px" }}>
      {/* Header */}
      {transaction && (
        <div style={{
          background: "#111120", border: "1px solid #1e1a33",
          borderRadius: "12px", padding: "16px 20px", marginBottom: "20px",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div>
            <div style={{ fontSize: "11px", color: "#5a4f7a", letterSpacing: "0.1em" }}>TRANSACTION</div>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#fff", marginTop: "4px" }}>
              {transaction.transaction_id}
            </div>
            <div style={{ fontSize: "13px", color: "#a89bc2", marginTop: "2px" }}>
              {transaction.merchant} · ${Number(transaction.amount).toFixed(2)}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "13px", color: "#f472b6", fontWeight: 600 }}>{analysis.fraud_pattern}</div>
            <div style={{ fontSize: "11px", color: "#5a4f7a", marginTop: "4px" }}>
              Probability: <span style={{ color: color }}>{analysis.fraud_probability}</span>
            </div>
          </div>
        </div>
      )}

      {/* Score + Customer Message */}
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "16px", marginBottom: "20px" }}>
        <div style={{
          background: "#111120", border: `1px solid ${color}33`,
          borderRadius: "12px", padding: "20px",
          display: "flex", alignItems: "center", gap: "16px",
        }}>
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="#1e1a33" strokeWidth="8" />
            <circle cx="60" cy="60" r="52" fill="none" stroke={color} strokeWidth="8"
              strokeDasharray={circ} strokeDashoffset={offset}
              strokeLinecap="round" transform="rotate(-90 60 60)" />
            <text x="60" y="54" textAnchor="middle" fill="#fff" fontSize="22" fontWeight="bold" fontFamily="monospace">{score}</text>
            <text x="60" y="70" textAnchor="middle" fill={color} fontSize="9" fontFamily="monospace" letterSpacing="2">
              {score >= 80 ? "CRITICAL" : score >= 60 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW"}
            </text>
          </svg>
          <div>
            <div style={{ fontSize: "10px", color: "#5a4f7a", letterSpacing: "0.12em" }}>RISK SCORE</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color }}>{score}/100</div>
            <div style={{ fontSize: "11px", color: "#7c6f9e", marginTop: "4px" }}>
              Confidence: <span style={{ color: "#c084fc" }}>{analysis.confidence}</span>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "10px", padding: "14px 16px", flex: 1 }}>
            <div style={{ fontSize: "10px", color: "#5a4f7a", letterSpacing: "0.1em", marginBottom: "6px" }}>CUSTOMER ALERT</div>
            <div style={{ fontSize: "13px", color: "#d4cfe8", lineHeight: 1.6 }}>💬 {analysis.customer_message}</div>
          </div>

          {ragSources.length > 0 && (
            <div style={{ background: "#0d1a1a", border: "1px solid #1a3a2a", borderRadius: "10px", padding: "12px 16px" }}>
              <div style={{ fontSize: "10px", color: "#2d7a5a", letterSpacing: "0.1em", marginBottom: "6px" }}>
                🧠 RAG SOURCES USED
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                {ragSources.map((s) => (
                  <span key={s} style={{
                    fontSize: "10px", padding: "2px 8px", borderRadius: "10px",
                    background: "#1a3a2a", color: "#4ade80", border: "1px solid #2d7a5a40",
                  }}>{s}</span>
                ))}
              </div>
            </div>
          )}

          {analysis.sar_required && (
            <div style={{
              background: "#ff475712", border: "1px solid #ff475740",
              borderRadius: "10px", padding: "12px 16px",
              display: "flex", gap: "10px", alignItems: "center",
            }}>
              <div style={{ fontSize: "20px" }}>📋</div>
              <div>
                <div style={{ fontSize: "11px", color: "#ff4757", fontWeight: 600, letterSpacing: "0.08em" }}>
                  SAR FILING REQUIRED
                </div>
                <div style={{ fontSize: "11px", color: "#a89bc2", marginTop: "2px" }}>{analysis.sar_reason}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "4px", marginBottom: "16px" }}>
        {["explanation", "actions", "recovery", "technical"].map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: "8px 16px", borderRadius: "8px", border: "1px solid",
            borderColor: activeTab === tab ? "#7c3aed" : "#1e1a33",
            background: activeTab === tab ? "#1a1230" : "transparent",
            color: activeTab === tab ? "#c084fc" : "#5a4f7a",
            cursor: "pointer", fontSize: "11px", letterSpacing: "0.08em",
            fontFamily: "inherit", textTransform: "uppercase",
          }}>
            {tab}
          </button>
        ))}
      </div>

      <div style={{ background: "#111120", border: "1px solid #1e1a33", borderRadius: "12px", padding: "22px" }}>
        {activeTab === "explanation" && (
          <div>
            <Label>FRAUD EXPLANATION</Label>
            <p style={{ fontSize: "14px", color: "#d4cfe8", lineHeight: 1.8, margin: "0 0 16px" }}>{analysis.explanation}</p>
            <div style={{ background: "#0d0d18", border: "1px solid #2a1f4a", borderRadius: "8px", padding: "14px", borderLeft: "3px solid #7c3aed" }}>
              <Label>RAG-INFORMED REASONING</Label>
              <p style={{ fontSize: "13px", color: "#a89bc2", lineHeight: 1.6, margin: 0 }}>{analysis.rag_reasoning}</p>
            </div>
            {analysis.similar_patterns?.length > 0 && (
              <div style={{ marginTop: "14px" }}>
                <Label>SIMILAR PATTERNS</Label>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {analysis.similar_patterns.map((p) => (
                    <span key={p} style={{
                      fontSize: "11px", padding: "4px 12px", borderRadius: "20px",
                      background: "#7c3aed22", color: "#c084fc", border: "1px solid #7c3aed44",
                    }}>{p}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "actions" && (
          <div>
            <Label>IMMEDIATE ACTION PLAN</Label>
            {(analysis.immediate_actions || []).map((action, i) => (
              <div key={i} style={{
                display: "flex", gap: "14px", alignItems: "flex-start",
                padding: "12px 0", borderBottom: i < analysis.immediate_actions.length - 1 ? "1px solid #1e1a33" : "none",
              }}>
                <div style={{
                  width: 26, height: 26, borderRadius: "50%", flexShrink: 0,
                  background: `hsl(${270 - i * 25}, 60%, 40%)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "12px", fontWeight: 700, color: "#fff",
                }}>{i + 1}</div>
                <div style={{ fontSize: "13px", color: "#d4cfe8", lineHeight: 1.6 }}>{action}</div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "recovery" && (
          <div>
            <Label>CUSTOMER RECOVERY STEPS</Label>
            {(analysis.recovery_steps || []).map((step, i) => (
              <div key={i} style={{
                display: "flex", gap: "12px", alignItems: "flex-start",
                padding: "12px 0", borderBottom: i < analysis.recovery_steps.length - 1 ? "1px solid #1e1a33" : "none",
              }}>
                <span style={{ fontSize: "16px" }}>
                  {["🔒", "📞", "💳", "🔑", "📄"][i] || "✅"}
                </span>
                <div style={{ fontSize: "13px", color: "#d4cfe8", lineHeight: 1.6 }}>{step}</div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "technical" && (
          <div>
            <Label>ANALYST TECHNICAL BRIEF</Label>
            <p style={{ fontSize: "13px", color: "#d4cfe8", lineHeight: 1.8, margin: "0 0 16px" }}>{analysis.technical_details}</p>
            {analysis.sar_required && (
              <div style={{
                background: "#ff475710", border: "1px solid #ff475740",
                borderRadius: "8px", padding: "14px",
              }}>
                <div style={{ fontSize: "11px", color: "#ff4757", fontWeight: 600, letterSpacing: "0.08em", marginBottom: "6px" }}>
                  SAR FILING DETAILS
                </div>
                <div style={{ fontSize: "12px", color: "#a89bc2", lineHeight: 1.6 }}>{analysis.sar_reason}</div>
              </div>
            )}
          </div>
        )}
      </div>
      </div>

      {/* Right: Chat Panel */}
      <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <Chat transaction={transaction} analysis={analysis} conversationId={null} />
      </div>
    </div>
  );
}

function AnalysisLoader() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60vh", gap: "20px" }}>
      <div style={{
        width: 56, height: 56, borderRadius: "50%",
        border: "3px solid #2a1f4a", borderTopColor: "#a855f7",
        animation: "spin 0.8s linear infinite",
      }} />
      <div style={{ fontSize: "12px", color: "#7c6f9e", letterSpacing: "0.15em" }}>QUERYING FAISS · GROQ LLM ANALYZING...</div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function EmptyState({ mode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60vh", gap: "16px", color: "#3a2f5a" }}>
      <div style={{ fontSize: "48px" }}>
        {mode === "structured" ? "🤖" : mode === "text" ? "📝" : "📄"}
      </div>
      <div style={{ fontSize: "13px", letterSpacing: "0.1em" }}>
        {mode === "structured" ? "Generate transactions, then click one to analyze" : mode === "text" ? "Enter transaction text and click analyze" : "Upload a PDF file to analyze transactions"}
      </div>
    </div>
  );
}
