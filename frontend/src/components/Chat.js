import { useState, useRef, useEffect } from "react";
import { chatAboutTransaction } from "../utils/api";

export default function Chat({ transaction, analysis, conversationId: initialConvId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(initialConvId);
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);

    // Add user message to UI
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await chatAboutTransaction(
        transaction,
        analysis,
        conversationId,
        userMessage
      );

      // Update conversation ID if new conversation was created
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.response },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error.message || "Failed to get response"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        borderRadius: "12px",
        background: "#0d0d18",
        border: "1px solid #1e1a33",
        overflow: "hidden",
      }}
    >
      {/* Chat Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #1e1a33",
          background: "#0a0a14",
        }}
      >
        <div style={{ fontSize: "12px", fontWeight: 600, color: "#c084fc" }}>
          💬 ASK ABOUT THIS TRANSACTION
        </div>
        <div style={{ fontSize: "10px", color: "#6b5f8a", marginTop: "4px" }}>
          Get context, answers, and expert insights
        </div>
      </div>

      {/* Messages Container */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "12px 16px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              color: "#6b5f8a",
              fontSize: "12px",
              textAlign: "center",
            }}
          >
            <div>
              <div style={{ fontSize: "24px", marginBottom: "8px" }}>🤔</div>
              <div>Ask anything about this transaction analysis</div>
              <div style={{ fontSize: "10px", marginTop: "4px" }}>
                E.g., "Why is this flagged?", "What should I do?"
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  marginBottom: "4px",
                }}
              >
                <div
                  style={{
                    maxWidth: "85%",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    background:
                      msg.role === "user"
                        ? "linear-gradient(135deg, #7c3aed, #8b5cf6)"
                        : "#1a1230",
                    border:
                      msg.role === "user"
                        ? "1px solid #7c3aed"
                        : "1px solid #2e2847",
                    color: msg.role === "user" ? "#fff" : "#c0c0c0",
                    fontSize: "12px",
                    lineHeight: "1.4",
                    wordWrap: "break-word",
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-start",
                  marginBottom: "4px",
                }}
              >
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: "8px",
                    background: "#1a1230",
                    border: "1px solid #2e2847",
                    color: "#6b5f8a",
                    fontSize: "11px",
                  }}
                >
                  AI thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div
        style={{
          padding: "12px",
          borderTop: "1px solid #1e1a33",
          background: "#0a0a14",
          display: "flex",
          gap: "8px",
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question..."
          disabled={loading}
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: "6px",
            border: "1px solid #2e2847",
            background: "#0d0d18",
            color: "#fff",
            fontSize: "12px",
            resize: "none",
            height: "40px",
            fontFamily: "inherit",
            outline: "none",
            transition: "all 0.2s",
            opacity: loading ? 0.6 : 1,
          }}
          onFocus={(e) => {
            e.target.style.borderColor = "#7c3aed";
            e.target.style.boxShadow = "0 0 8px rgba(124, 58, 237, 0.2)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "#2e2847";
            e.target.style.boxShadow = "none";
          }}
        />
        <button
          onClick={handleSendMessage}
          disabled={loading || !input.trim()}
          style={{
            padding: "0 12px",
            borderRadius: "6px",
            border: "1px solid #7c3aed",
            background: loading || !input.trim() ? "#2e2847" : "#7c3aed",
            color: "#fff",
            fontSize: "12px",
            fontWeight: 600,
            cursor: loading || !input.trim() ? "default" : "pointer",
            transition: "all 0.2s",
            opacity: loading || !input.trim() ? 0.5 : 1,
            whiteSpace: "nowrap",
          }}
          onMouseEnter={(e) => {
            if (!loading && input.trim()) {
              e.target.style.background = "#8b5cf6";
            }
          }}
          onMouseLeave={(e) => {
            if (!loading && input.trim()) {
              e.target.style.background = "#7c3aed";
            }
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
