import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";

function ChatWindow({ messages, onSend, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-icon">
              <i className="bi bi-stars"></i>
            </div>

            <h2>What would you like to know?</h2>

            <p>
              Ask questions about your uploaded documents.
              Knowledge AI will find relevant information and explain it.
            </p>

            <div className="suggestion-list">
              <span>Try asking:</span>
              <button onClick={() => onSend("What is this document about?")}>
                What is this document about?
              </button>

              <button onClick={() => onSend("Summarize the important points.")}>
                Summarize the important points
              </button>

              <button onClick={() => onSend("What are the eligibility criteria?")}>
                What are the eligibility criteria?
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble
              key={message.message_id || index}
              message={message}
            />
          ))
        )}

        {loading && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
            <small>Knowledge AI is thinking...</small>
          </div>
        )}

        <div ref={bottomRef}></div>
      </div>

      <div className="chat-input-wrapper">
        <ChatInput onSend={onSend} loading={loading} />
      </div>
    </div>
  );
}

export default ChatWindow;