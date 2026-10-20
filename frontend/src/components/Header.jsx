import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import Navbar from "react-bootstrap/Navbar";
import Nav from "react-bootstrap/Nav";
import Container from "react-bootstrap/Container";

import { useAuth } from "../context/AuthContext";
import { useUI } from "../context/UIContext";
import { useToast } from "../context/ToastContext";
import { roleLabel } from "../lib/format";

export default function Header() {
  const { isAuthenticated, canManage, user, logout } = useAuth();
  const { openAuth } = useUI();
  const toast = useToast();
  const [expanded, setExpanded] = useState(false);

  const close = () => setExpanded(false);

  const handleLogout = () => {
    logout();
    toast.push("Sesión cerrada", "", "success");
    close();
  };

  return (
    <Navbar
      expand="lg"
      expanded={expanded}
      onToggle={setExpanded}
      fixed="top"
      className="ca-header"
      collapseOnSelect
    >
      <Container>
        <Navbar.Brand as={Link} to="/" className="ca-logo" onClick={close}>
          <span className="ca-logo-mark">🎬</span>
          <span className="ca-logo-text">
            CINE<span>ARCADE</span>
          </span>
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="main-nav" className="ca-hamburger" />

        <Navbar.Collapse id="main-nav">
          <Nav className="me-auto ca-nav">
            <Nav.Link as={NavLink} to="/" end onClick={close}>
              Cartelera
            </Nav.Link>
            <Nav.Link as={NavLink} to="/funciones" onClick={close}>
              Funciones
            </Nav.Link>
            {isAuthenticated && (
              <Nav.Link as={NavLink} to="/mis-entradas" onClick={close}>
                Mis entradas
              </Nav.Link>
            )}
            {canManage && (
              <>
                <Nav.Link as={NavLink} to="/dashboard" onClick={close}>
                  Dashboard
                </Nav.Link>
                <Nav.Link as={NavLink} to="/admin" onClick={close}>
                  Gestión
                </Nav.Link>
              </>
            )}
          </Nav>

          <div className="ca-header-actions">
            {isAuthenticated ? (
              <>
                <span className="ca-user-name" title={user?.email}>
                  {user?.username}
                  <span className={`ca-role-badge ca-role-${user?.role}`}>{roleLabel(user?.role)}</span>
                </span>
                <button type="button" className="ca-btn ca-btn-ghost ca-btn-sm" onClick={handleLogout}>
                  Salir
                </button>
              </>
            ) : (
              <button
                type="button"
                className="ca-btn ca-btn-primary ca-btn-sm"
                onClick={() => {
                  openAuth("login");
                  close();
                }}
              >
                Iniciar sesión
              </button>
            )}
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
