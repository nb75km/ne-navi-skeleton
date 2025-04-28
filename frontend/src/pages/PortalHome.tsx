import React from "react";
import { Link } from "react-router-dom";
import ServiceHealth from "../components/ServiceHealth";

export default function PortalHome() {
  return (
    <div className="p-4 space-y-6">
      <h1 className="text-2xl font-bold">NE Navi Portal</h1>

      {/* サービスステータスカード（リンク付き） */}
      <div className="flex flex-wrap gap-4">
        <ServiceHealth label="Chat Explorer" path="/chat/health" to="/chat" />
        <ServiceHealth
          label="Minutes Maker"
          path="/minutes/health"
          to="/minutes"
        />
      </div>

      {/* 従来のテキストリンク群（任意で残す／削除可） */}
      <div className="space-x-4">
        <Link
          to="/chat"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-xl shadow transition"
        >
          Chat Explorer →
        </Link>
        <Link
          to="/minutes"
          className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium px-4 py-2 rounded-xl shadow transition"
        >
          Minutes Maker →
        </Link>
      </div>
    </div>
  );
}
