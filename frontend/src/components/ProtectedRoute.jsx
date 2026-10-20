import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import Spinner from "react-bootstrap/Spinner";

import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

/**
 * Protege rutas privadas.
 *
 * - `admin` exige rol de administrador (informático).
 * - `roles` admite una lista de roles permitidos, p. ej.
 *   `roles={["manager", "admin"]}` para el personal de la casa.
 */
export default function ProtectedRoute({ children, admin = false, roles = null, message }) {
  const { ready, isAuthenticated, isAdmin, role } = useAuth();
  const toast = useToast();

  const allowed =
    isAuthenticated && (!admin || isAdmin) && (!roles || roles.includes(role));
  const blocked = ready && !allowed;

  useEffect(() => {
    if (blocked && message) toast.push("Acceso restringido", message, "error");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blocked]);

  if (!ready) {
    return (
      <div className="ca-loading">
        <Spinner animation="border" role="status" />
        <span className="visually-hidden">Cargando…</span>
      </div>
    );
  }

  if (blocked) return <Navigate to="/" replace />;

  return children;
}
