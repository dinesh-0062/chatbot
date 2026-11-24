import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import ChatPage from "./pages/chatpage";
import DocumentsPage from "./pages/DocumentsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;