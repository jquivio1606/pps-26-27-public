import { useCallback, useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Card from "react-bootstrap/Card";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import Table from "react-bootstrap/Table";

import { api } from "../api/client";
import { fmtDate, roleLabel } from "../lib/format";
import SectionHeader from "../components/SectionHeader";
import AdminTabs from "../components/AdminTabs";
import PaginationBar from "../components/PaginationBar";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

const PAGE_SIZE = 10;
const ROLES = ["user", "manager", "admin"];

export default function UsersPage() {
  const toast = useToast();
  const { user: currentUser } = useAuth();
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [pwdTarget, setPwdTarget] = useState(null);
  const [pwd, setPwd] = useState("");
  const [pwd2, setPwd2] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setData(await api(`/auth/users?page=${page}&size=${PAGE_SIZE}`));
    } catch (err) {
      setError(err.message);
    }
  }, [page]);

  useEffect(() => {
    load();
  }, [load]);

  const changeRole = async (target, role) => {
    if (role === target.role) return;
    try {
      await api(`/auth/users/${target.id}`, { method: "PATCH", body: { role } });
      toast.push("Rol actualizado", `${target.username} → ${roleLabel(role)}`, "success");
      await load();
    } catch (err) {
      toast.push("No se pudo cambiar el rol", err.message, "error");
      await load();
    }
  };

  const submitPassword = async (e) => {
    e.preventDefault();
    if (pwd !== pwd2) {
      toast.push(
        "Las contraseñas no coinciden",
        "Escribe la misma contraseña en los dos campos.",
        "error",
      );
      return;
    }
    setBusy(true);
    try {
      await api(`/auth/users/${pwdTarget.id}/password`, {
        method: "POST",
        body: { password: pwd },
      });
      toast.push("Contraseña restablecida", pwdTarget.username, "success");
      closePasswordModal();
    } catch (err) {
      toast.push("No se pudo restablecer la contraseña", err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  const openPasswordModal = (target) => {
    setPwd("");
    setPwd2("");
    setPwdTarget(target);
  };

  const closePasswordModal = () => {
    setPwdTarget(null);
    setPwd("");
    setPwd2("");
  };

  const removeUser = async (target) => {
    if (!window.confirm(`¿Eliminar la cuenta de "${target.username}"?`)) return;
    try {
      await api(`/auth/users/${target.id}`, { method: "DELETE" });
      toast.push("Usuario eliminado", target.username, "success");
      await load();
    } catch (err) {
      toast.push("No se pudo eliminar el usuario", err.message, "error");
    }
  };

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="ZONA ADMIN"
          title="Usuarios"
          sub="Gestiona cuentas y roles. Las contraseñas se guardan siempre cifradas (bcrypt)."
        />
        <AdminTabs />

        {error && <div className="ca-empty">No se pudieron cargar los usuarios: {error}</div>}

        <Card className="ca-card">
          <Card.Body>
            <div className="ca-table-wrap">
              <Table responsive borderless className="ca-table align-middle">
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Alta</th>
                    <th className="text-end">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.items || []).map((u) => {
                    const isSelf = u.id === currentUser?.id;
                    return (
                      <tr key={u.id}>
                        <td>
                          #{u.id} · {u.username}
                          {isSelf && <span className="ca-table-sub"> (tú)</span>}
                        </td>
                        <td>{u.email}</td>
                        <td>
                          <Form.Select
                            size="sm"
                            className="ca-role-select"
                            value={u.role}
                            onChange={(e) => changeRole(u, e.target.value)}
                            aria-label={`Rol de ${u.username}`}
                          >
                            {ROLES.map((role) => (
                              <option key={role} value={role}>
                                {roleLabel(role)}
                              </option>
                            ))}
                          </Form.Select>
                        </td>
                        <td>{fmtDate(u.created_at).full}</td>
                        <td className="text-end ca-row-actions">
                          <button
                            type="button"
                            className="ca-btn ca-btn-outline ca-btn-sm"
                            onClick={() => openPasswordModal(u)}
                            title="Restablecer la contraseña de este usuario"
                          >
                            Contraseña
                          </button>
                          <button
                            type="button"
                            className="ca-btn ca-btn-ghost ca-btn-sm"
                            onClick={() => removeUser(u)}
                            disabled={isSelf}
                            title={isSelf ? "No puedes eliminar tu propia cuenta" : "Eliminar"}
                          >
                            Eliminar
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </div>

            <PaginationBar data={data} onChange={setPage} ariaLabel="Paginación de usuarios" />
          </Card.Body>
        </Card>
      </Container>

      <Modal
        show={!!pwdTarget}
        onHide={closePasswordModal}
        centered
        className="ca-modal"
      >
        <Modal.Body>
          <h4 className="ca-booking-title">Nueva contraseña</h4>
          <p className="ca-kpi-note">
            Se guardará cifrada con bcrypt para <b>{pwdTarget?.username}</b>. Confírmala escribiéndola
            dos veces.
          </p>
          <Form onSubmit={submitPassword}>
            <Form.Group className="mb-3">
              <Form.Label className="ca-field-label">Nueva contraseña</Form.Label>
              <Form.Control
                type="password"
                required
                minLength={6}
                maxLength={72}
                value={pwd}
                onChange={(e) => setPwd(e.target.value)}
                autoComplete="new-password"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label className="ca-field-label">Repite la contraseña</Form.Label>
              <Form.Control
                type="password"
                required
                minLength={6}
                maxLength={72}
                value={pwd2}
                onChange={(e) => setPwd2(e.target.value)}
                autoComplete="new-password"
                isInvalid={pwd2.length > 0 && pwd !== pwd2}
              />
              <Form.Control.Feedback type="invalid">
                Las contraseñas no coinciden.
              </Form.Control.Feedback>
            </Form.Group>
            <div className="ca-form-actions">
              <button
                type="submit"
                className="ca-btn ca-btn-primary"
                disabled={busy || pwd !== pwd2}
              >
                {busy ? "Guardando…" : "Restablecer contraseña"}
              </button>
              <button
                type="button"
                className="ca-btn ca-btn-ghost"
                onClick={closePasswordModal}
              >
                Cancelar
              </button>
            </div>
          </Form>
        </Modal.Body>
      </Modal>
    </section>
  );
}
