/* -----------------------------------------------------------------------------
 * src/components/ui/Navbar.tsx
 * シンプルなトップバー。
 *  - ログイン中   : メールアドレス + Logout ボタン + メインナビゲーション
 *  - 未ログイン時 : Login ボタンのみ
 *  - Tailwind CSS v3 でスタイリング
 * ---------------------------------------------------------------------------*/

import React from "react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const navItems = [
  { href: "/chat", label: "Chat" },
  { href: "/minutes", label: "Minutes" },
];

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-slate-800 text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">
        {/* ---------- Brand ---------- */}
        <Link to="/" className="text-lg font-semibold hover:opacity-80">
          NE&nbsp;Navi
        </Link>

        {/* ---------- Main navigation (表示はログイン時のみ) ---------- */}
        {user && (
          <nav className="ml-6 hidden gap-6 md:flex">
            {navItems.map(({ href, label }) => (
              <NavLink
                key={href}
                to={href}
                className={({ isActive }) =>
                  `text-sm transition-opacity duration-150 hover:opacity-80 ${
                    isActive ? "font-bold" : "opacity-70"
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        )}

        {/* ---------- Right area ---------- */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <span className="hidden text-sm md:inline">{user.email}</span>
              <button
                onClick={logout}
                className="rounded bg-slate-700 px-3 py-1 text-sm transition-colors hover:bg-slate-600"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/auth/login"
              className="rounded bg-indigo-600 px-3 py-1 text-sm transition-colors hover:bg-indigo-500"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
