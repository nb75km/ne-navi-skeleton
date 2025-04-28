import React from "react";
import { HashRouter as Router, Routes, Route } from "react-router-dom";
import PortalHome from "./pages/PortalHome";
import ChatList from "./pages/ChatList";
import ChatDetail from "./pages/ChatDetail";
import MinutesList from "./pages/MinutesList";
// import TranscriptDetail from "./pages/TranscriptDetail";
import Workspace from "./pages/Workspace";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<PortalHome />} />
        <Route path="/chat" element={<ChatList />} />
        <Route path="/chat/:id" element={<ChatDetail />} />
        <Route path="/minutes" element={<MinutesList />} />
        {/* <Route path="/minutes/:id" element={<TranscriptDetail />} /> */}
        <Route path="/workspace/:tid" element={<Workspace />} />
      </Routes>
    </Router>
  );
}
