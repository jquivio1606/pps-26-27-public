import { useEffect, useState } from "react";
import Modal from "react-bootstrap/Modal";
import Form from "react-bootstrap/Form";

import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useUI } from "../context/UIContext";

export default function AuthModal() {
  const { authModal, closeAuth, resumePendingBooking } = useUI();
  const { login, register } = useAuth();
  const toast = useToast();

  const [tab, setTab] = useState(authModal.tab);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (authModal.open) setTab(authModal.tab);
  }, [authModal.open, authModal.tab]);

  const finish = (username) => {
    toast.push("Bienvenido/a", username, "success");
    closeAuth();
    resumePendingBooking();
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const f = e.target;
    setBusy(true);
    try {
      const me = await login(f.username.value, f.password.value);
      finish(me.username);
    } catch (err) {
      toast.push("No se pudo iniciar sesión", err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const f = e.target;
    setBusy(true);
    try {
      const me = await register({
        username: f.username.value,
        email: f.email.value,
        password: f.password.value,
      });
      toast.push("Cuenta creada", `¡Hola, ${me.username}!`, "success");
      closeAuth();
      resumePendingBooking();
    } catch (err) {
      toast.push("No se pudo registrar", err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show={authModal.open} onHide={closeAuth} centered className="ca-modal w-75">
      <Modal.Body>
        <div className="ca-tabs">
          <button
            type="button"
            className={`ca-tab${tab === "login" ? " active" : ""}`}
            onClick={() => setTab("login")}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            className={`ca-tab${tab === "register" ? " active" : ""}`}
            onClick={() => setTab("register")}
          >
            Registrarse
          </button>
        </div>

        {tab === "login" ? (
          <Form className="ca-auth-form" onSubmit={handleLogin}>
            <Form.Group className="mb-3">
              <Form.Label>Usuario</Form.Label>
              <Form.Control
                name="username"
                required
                autoComplete="username"
                placeholder="admin"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Contraseña</Form.Label>
              <Form.Control
                name="password"
                type="password"
                required
                autoComplete="current-password"
                placeholder="••••••"
              />
            </Form.Group>
            <button type="submit" className="ca-btn ca-btn-primary ca-btn-block" disabled={busy}>
              {busy ? "Entrando…" : "Entrar"}
            </button>
            <div className="ca-divider" style={{ margin: "16px 0", textAlign: "center", color: "#888" }}>
              <span>o</span>
            </div>
            <a
              href="/auth/github"
              className="ca-btn ca-btn-block"
              style={{ background: "#24292e", color: "#fff", textDecoration: "none", display: "block", textAlign: "center" }}
            >
              Iniciar sesión con GitHub
            </a>
            <p className="ca-hint">
              Prueba: <code>admin / admin123</code> · <code>user / user123</code>
            </p>
          </Form>
        ) : (
          <Form className="ca-auth-form" onSubmit={handleRegister}>
            <Form.Group className="mb-3">
              <Form.Label>Usuario</Form.Label>
              <Form.Control name="username" required minLength={3} maxLength={50} placeholder="tu_usuario" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control name="email" type="email" required placeholder="tu@email.com" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Contraseña</Form.Label>
              <Form.Control
                name="password"
                type="password"
                required
                minLength={6}
                maxLength={72}
                placeholder="mínimo 6 caracteres"
              />
            </Form.Group>
            <button type="submit" className="ca-btn ca-btn-primary ca-btn-block" disabled={busy}>
              {busy ? "Creando…" : "Crear cuenta"}
            </button>
          </Form>
        )}
      </Modal.Body>
    </Modal>
  );
}
