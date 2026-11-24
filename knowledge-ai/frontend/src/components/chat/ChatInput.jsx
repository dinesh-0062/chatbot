import { useState } from "react";

function ChatInput({ onSend, loading }) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) return;

    onSend(trimmedQuestion);
    setQuestion("");
  };

  return (
    <form className="chat-input-container" onSubmit={handleSubmit}>
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask anything about your uploaded documents..."
        rows="2"
        disabled={loading}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSubmit(event);
          }
        }}
      />

      <div className="chat-input-footer">
        <span>
          <i className="bi bi-shield-check"></i>
          Answers grounded in your documents
        </span>

        <button
          type="submit"
          disabled={!question.trim() || loading}
        >
          {loading ? (
            <span className="spinner-border spinner-border-sm"></span>
          ) : (
            <i className="bi bi-send-fill"></i>
          )}
          <span>{loading ? "Thinking..." : "Send"}</span>
        </button>
      </div>
    </form>
  );
}

export default ChatInput;