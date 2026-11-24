
import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <i className="bi bi-stars"></i>
        </div>
        <div>
          <h5>Knowledge AI</h5>
          <small>Document Intelligence</small>
        </div>
      </div>

      <div className="sidebar-section">
        <p className="sidebar-label">WORKSPACE</p>

        <NavLink to="/" end className={({ isActive }) =>
          `sidebar-link ${isActive ? "active" : ""}`
        }>
          <i className="bi bi-chat-square-text"></i>
          <span>AI Chat</span>
        </NavLink>

        <NavLink to="/documents" className={({ isActive }) =>
          `sidebar-link ${isActive ? "active" : ""}`
        }>
          <i className="bi bi-file-earmark-pdf"></i>
          <span>Documents</span>
        </NavLink>
      </div>

      <div className="sidebar-bottom">
        <div className="sidebar-profile">
          <div className="profile-avatar">K</div>
          <div>
            <strong>Knowledge User</strong>
            <small>Personal Workspace</small>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
