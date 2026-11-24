
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import api from "../../api/axios";

function Sidebar({ isOpen = false, onClose = () => {} }) {
  const [conversations, setConversations] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/conversations/")
      .then((response) => {
        setConversations(response.data.conversations || []);
      })
      .catch(() => setConversations([]));
  }, []);

  const openConversation = (conversationId) => {
    onClose();
    navigate("/");

    window.setTimeout(() => {
      window.dispatchEvent(
        new CustomEvent("knowledge-ai-open-conversation", {
          detail: conversationId,
        })
      );
    }, 0);
  };

  const handleNavigation = () => {
    onClose();
  };

  return (
    <>
      {isOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <motion.aside
        initial={false}
        animate={{ x: 0 }}
        className={`sidebar ${isOpen ? "sidebar-open" : ""}`}
      >
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="brand-icon">
            <i className="bi bi-stars"></i>
          </div>

          <div className="brand-content">
            <h5>Knowledge AI</h5>
            <small>Document Intelligence</small>
          </div>

          <button
            type="button"
            className="sidebar-close"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <i className="bi bi-x-lg"></i>
          </button>
        </div>

        {/* Workspace */}
        <div className="sidebar-section">
          <p className="sidebar-label">WORKSPACE</p>

          <NavLink
            to="/"
            end
            onClick={handleNavigation}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <i className="bi bi-chat-square-text"></i>
            <span>AI Chat</span>
          </NavLink>

          <NavLink
            to="/documents"
            onClick={handleNavigation}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <i className="bi bi-file-earmark-pdf"></i>
            <span>Documents</span>
          </NavLink>

          {/* Recent conversations */}
          {conversations.length > 0 && (
            <>
              <div className="conversation-heading">
                <p className="sidebar-label conversation-label">
                  RECENT CHATS
                </p>
                <span>{conversations.length}</span>
              </div>

              <div className="conversation-list">
                {conversations.slice(0, 8).map((conversation) => (
                  <button
                    type="button"
                    className="conversation-link"
                    key={conversation.conversation_id}
                    onClick={() =>
                      openConversation(conversation.conversation_id)
                    }
                    title={conversation.title}
                  >
                    <i className="bi bi-chat-left-text"></i>
                    <span>{conversation.title}</span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Bottom profile */}
        <div className="sidebar-bottom">
          <div className="sidebar-profile">
            <div className="profile-avatar">K</div>

            <div className="profile-details">
              <strong>Knowledge User</strong>
              <small>Personal Workspace</small>
            </div>

            <i className="bi bi-three-dots profile-menu-icon"></i>
          </div>
        </div>
      </motion.aside>
    </>
  );
}

export default Sidebar;
