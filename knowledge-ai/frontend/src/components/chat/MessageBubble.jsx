
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";

import SourceReferences from "./SourceReferences";

function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>

      {!isUser && (
        <div className="message-avatar assistant-avatar">
          <i className="bi bi-stars"></i>
        </div>
      )}

      <div className="message-content">

        <div className="message-author">
          {isUser ? "You" : "Knowledge AI"}
        </div>

        <div className={`message-bubble ${isUser ? "user-bubble" : "assistant-bubble"}`}>

          {isUser ? (
            <p className="mb-0">{message.content}</p>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
              >
                {message.content || ""}
              </ReactMarkdown>
            </div>
          )}

        </div>

        {!isUser && (
          <SourceReferences sources={message.sources || []} />
        )}

      </div>

      {isUser && (
        <div className="message-avatar user-avatar">
          <i className="bi bi-person"></i>
        </div>
      )}

    </div>
  );
}

export default MessageBubble;
