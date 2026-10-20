import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

import { useAuth } from "./AuthContext";
import { useToast } from "./ToastContext";

/**
 * Contexto de interfaz: gestiona los modales globales (ficha de película,
 * autenticación y compra). Así cualquier componente puede abrirlos sin
 * duplicar estado.
 */
const UIContext = createContext(null);

export function UIProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const toast = useToast();

  const [authModal, setAuthModal] = useState({ open: false, tab: "login" });
  const [movieId, setMovieId] = useState(null);
  const [bookingId, setBookingId] = useState(null);
  const pendingBooking = useRef(null);

  const openAuth = useCallback((tab = "login") => setAuthModal({ open: true, tab }), []);
  const closeAuth = useCallback(() => setAuthModal((s) => ({ ...s, open: false })), []);

  const openMovie = useCallback((id) => setMovieId(id), []);
  const closeMovie = useCallback(() => setMovieId(null), []);

  const openBooking = useCallback(
    (id) => {
      if (!isAuthenticated) {
        pendingBooking.current = id;
        toast.push("Inicia sesión", "Necesitas una cuenta para comprar entradas.");
        openAuth("login");
        return;
      }
      setBookingId(id);
    },
    [isAuthenticated, openAuth, toast]
  );

  const closeBooking = useCallback(() => setBookingId(null), []);

  // Tras autenticarse, continúa la compra que quedó pendiente.
  const resumePendingBooking = useCallback(() => {
    const id = pendingBooking.current;
    pendingBooking.current = null;
    if (id != null) setBookingId(id);
  }, []);

  const value = useMemo(
    () => ({
      authModal,
      openAuth,
      closeAuth,
      movieId,
      openMovie,
      closeMovie,
      bookingId,
      openBooking,
      closeBooking,
      resumePendingBooking,
    }),
    [
      authModal,
      openAuth,
      closeAuth,
      movieId,
      openMovie,
      closeMovie,
      bookingId,
      openBooking,
      closeBooking,
      resumePendingBooking,
    ]
  );

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>;
}

export function useUI() {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error("useUI debe usarse dentro de <UIProvider>");
  return ctx;
}
