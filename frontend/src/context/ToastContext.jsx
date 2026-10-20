import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const counter = useRef(0);

  const remove = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (title, message = "", type = "") => {
      const id = ++counter.current;
      setToasts((list) => [...list, { id, title, message, type }]);
      setTimeout(() => remove(id), 3800);
      return id;
    },
    [remove]
  );

  const value = useMemo(() => ({ toasts, push, remove }), [toasts, push, remove]);
  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast debe usarse dentro de <ToastProvider>");
  return ctx;
}
