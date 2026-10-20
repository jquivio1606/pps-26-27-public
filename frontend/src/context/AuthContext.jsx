import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, setAuthToken, setUnauthorizedHandler } from "../api/client";

const TOKEN_KEY = "cine_token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // El token se inyecta en el cliente HTTP en cuanto cambia.
  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const persistToken = useCallback((value) => {
    setToken(value || null);
    if (value) localStorage.setItem(TOKEN_KEY, value);
    else localStorage.removeItem(TOKEN_KEY);
  }, []);

  const logout = useCallback(() => {
    persistToken(null);
    setUser(null);
  }, [persistToken]);

  // Si la API responde 401 (token caducado) cerramos la sesión.
  useEffect(() => {
    setUnauthorizedHandler(() => logout());
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  // Restaura la sesión al cargar comprobando el token guardado.
  useEffect(() => {
    let active = true;
    if (!token) {
      setUser(null);
      setReady(true);
      return;
    }
    (async () => {
      try {
        const me = await api("/auth/me");
        if (active) setUser(me);
      } catch {
        if (active) logout();
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
    };
    // Solo al montar: el resto de cambios de token los gestiona login/logout.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (username, password) => {
      const data = await api("/auth/login", {
        method: "POST",
        form: true,
        body: { username, password },
      });
      persistToken(data.access_token);
      setAuthToken(data.access_token);
      const me = await api("/auth/me");
      setUser(me);
      setReady(true);
      return me;
    },
    [persistToken]
  );

  const register = useCallback(
    async ({ username, email, password }) => {
      await api("/auth/register", { method: "POST", body: { username, email, password } });
      return login(username, password);
    },
    [login]
  );

  const value = useMemo(
    () => ({
      token,
      user,
      ready,
      isAuthenticated: !!user,
      role: user?.role || null,
      isAdmin: user?.role === "admin",
      isManager: user?.role === "manager",
      // Personal de la casa: el jefe (manager) y el informático (admin).
      canManage: user?.role === "manager" || user?.role === "admin",
      login,
      register,
      logout,
    }),
    [token, user, ready, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
