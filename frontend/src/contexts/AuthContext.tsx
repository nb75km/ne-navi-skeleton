import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { api } from "../lib/api";

/* ------------------------------------------------------------------ */
/* 型定義                                                              */
/* ------------------------------------------------------------------ */

/** Back-end が返す UserRead 型を最小限で写したもの */
interface User {
  id: string;
  email: string;
}

/** Context で供給する値 */
interface AuthCtxValue {
  /** ログイン済みならユーザー情報、未ログインなら null */
  user: User | null;
  /** /users/me を呼んでログイン状態を再判定 */
  reload: () => Promise<void>;
  /** Cookie を破棄してログアウト */
  logout: () => Promise<void>;
}

/* ------------------------------------------------------------------ */
/* Context                                                             */
/* ------------------------------------------------------------------ */

const AuthContext = createContext<AuthCtxValue>({
  user: null,
  reload: async () => {},
  logout: async () => {},
});

/**
 * <AuthProvider> — アプリ全体をラップして認証状態を共有
 */
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  /* ---------- ヘルパ ---------- */

  /** /users/me を叩いて現在のユーザーを取得（未ログインなら 401 → user=null） */
  const reload = async () => {
    try {
      const me = await api.get<User>("/users/me");  // Cookie が自動送信される
      setUser(me);
    } catch {
      setUser(null);
    }
  };

  /** /auth/jwt/logout で Cookie を無効化し、state を空にする */
  const logout = async () => {
    try {
      await api.post("/auth/jwt/logout");
    } finally {
      setUser(null);
    }
  };

  /* ---------- 起動時に一度だけ /users/me ---------- */
  useEffect(() => {
    void reload();
  }, []);

  return (
    <AuthContext.Provider value={{ user, reload, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

/* ------------------------------------------------------------------ */
/* Hook                                                                */
/* ------------------------------------------------------------------ */

export const useAuth = () => useContext(AuthContext);
