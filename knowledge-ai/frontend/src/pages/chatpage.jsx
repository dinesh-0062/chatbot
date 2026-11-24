import { useEffect, useState } from "react";
import api from "../api/axios";
import Layout from "../components/layout/Layout";
import ChatWindow from "../components/chat/ChatWindow";

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedConversationId = localStorage.getItem("knowledge-ai-conversation");
    if (!savedConversationId) return;

    api.get(`/conversations/${savedConversationId}`)
      .then((response) => {
        setConversationId(savedConversationId);
        setMessages(response.data.conversation?.messages || []);
      })
      .catch(() => {
        localStorage.removeItem("knowledge-ai-conversation");
      });
  }, []);

  useEffect(() => {
    const openConversation = (event) => {
      const id = event.detail;
      api.get(`/conversations/${id}`)
        .then((response) => {
          setConversationId(id);
          localStorage.setItem("knowledge-ai-conversation", id);
          setMessages(response.data.conversation?.messages || []);
          setError("");
        })
        .catch((err) => {
          setError(err.response?.data?.detail || "Could not restore this conversation.");
        });
    };
    window.addEventListener("knowledge-ai-open-conversation", openConversation);
    return () => window.removeEventListener("knowledge-ai-open-conversation", openConversation);
  }, []);

  const sendMessage = async (question) => {
    if (loading) return;

    const userMessage = {
      role: "user",
      content: question,
    };

    setMessages((previous) => [...previous, userMessage]);
    setLoading(true);
    setError("");

    try {
      const response = await api.post("/chat/ask", {
        question,
        top_k: 5,
        conversation_id: conversationId,
      });

      const data = response.data;

      if (!data.success) {
        throw new Error("Unable to generate an answer.");
      }

      setConversationId(data.conversation_id);
      localStorage.setItem("knowledge-ai-conversation", data.conversation_id);

      setMessages((previous) => [
        ...previous,
        {
          message_id: data.messages?.assistant_message_id,
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
        },
      ]);
    } catch (err) {
      console.error("Chat error:", err);

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    if (loading) return;

    setMessages([]);
    setConversationId(null);
    setError("");
    localStorage.removeItem("knowledge-ai-conversation");
  };

  return (
    <Layout>
      <div className="chat-page">
        <div className="chat-page-header">
          <div>
            <h2>AI Assistant</h2>
            <p>Ask questions and get answers from your documents.</p>
          </div>

          <button
            className="new-chat-button"
            onClick={startNewChat}
            disabled={loading}
          >
            <i className="bi bi-plus-lg"></i>
            New Chat
          </button>
        </div>

        {error && (
          <div className="alert alert-danger mx-3 mt-2">
            {error}
          </div>
        )}

        <ChatWindow
          messages={messages}
          onSend={sendMessage}
          loading={loading}
        />
      </div>
    </Layout>
  );
}

export default ChatPage;