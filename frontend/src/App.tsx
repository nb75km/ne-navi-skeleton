import React from "react";
import { QueryProvider } from "./lib/queryClient";
import {
  HashRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import PortalHome from "./pages/PortalHome";
import ChatList from "./pages/ChatList";
import ChatDetail from "./pages/ChatDetail";
import MinutesList from "./pages/MinutesList";
import TranscriptDiff from "./pages/TranscriptDiff";
import Workspace from "./pages/Workspace";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";

/* ────────────────────────────────────────
 * 認可ガード : 未ログインなら /auth/login へ
 * ──────────────────────────────────────── */
function Private({ children }: { children: JSX.Element }) {
  const {user} = useAuth();
  return user ? children : <Navigate to="/auth/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <QueryProvider>
        <Router>
          <Routes>
            {/* ──────── 公開ルート ──────── */}
            <Route path="/auth/login" element={<Login />} />
            <Route path="/auth/register" element={<Register />} />

            {/* ──────── 認可必須ルート ──────── */}
            <Route path="/" element={<Private><PortalHome /></Private>} />
            <Route path="/chat" element={<Private><ChatList /></Private>} />
            <Route path="/chat/:id" element={<Private><ChatDetail /></Private>} />
            <Route path="/minutes" element={<Private><MinutesList /></Private>} />
            <Route path="/workspace/:tid" element={<Private><Workspace /></Private>} />
            <Route path="/minutes/:id/diff" element={<Private><TranscriptDiff /></Private>} />

            {/* ──────── フォールバック ──────── */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </QueryProvider>
    </AuthProvider>
  );
}
