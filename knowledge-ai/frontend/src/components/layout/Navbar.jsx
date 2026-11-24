
import { useLocation } from "react-router-dom";

function Navbar() {
  const location = useLocation();

  const pageTitle =
    location.pathname === "/documents" ? "My Documents" : "AI Assistant";

  return (
    <header className="top-navbar">
      <div>
        <h5>{pageTitle}</h5>
        <p>Ask questions and explore your knowledge base.</p>
      </div>

      <div className="navbar-status">
        <span className="status-dot"></span>
        AI Workspace
      </div>
    </header>
  );
}

export default Navbar;
