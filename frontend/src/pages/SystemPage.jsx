import { useCallback, useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Card from "react-bootstrap/Card";

import { api } from "../api/client";
import SectionHeader from "../components/SectionHeader";
import AdminTabs from "../components/AdminTabs";

/**
 * Tecnologías del frontend. El backend informa de las suyas vía /stats/system;
 * estas se declaran aquí porque solo son conocidas por el propio frontend.
 */
const FRONTEND_TECHS = [
  { name: "React", version: "18.3.1", group: "Frontend", purpose: "Librería de interfaz" },
  { name: "React Router", version: "6.30.6", group: "Frontend", purpose: "Enrutado (SPA)" },
  { name: "React Bootstrap", version: "2.10.10", group: "Frontend", purpose: "Componentes de UI" },
  { name: "Bootstrap", version: "5.3.8", group: "Frontend", purpose: "Estilos y rejilla responsive" },
  { name: "Vite", version: "6.4.4", group: "Frontend", purpose: "Compilador y build de producción" },
];

const TECH_GROUPS = ["Servidor", "Datos", "Seguridad", "Frontend"];

export default function SystemPage() {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setInfo(await api("/stats/system"));
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const allHashed = info && info.users_hashed === info.users_total;
  const techs = info ? [...(info.technologies || []), ...FRONTEND_TECHS] : [];

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="ZONA ADMIN"
          title="Sistema"
          sub="Información técnica del servicio (sin exponer secretos)."
        />
        <AdminTabs />

        {error && <div className="ca-empty">No se pudo cargar el sistema: {error}</div>}

        {info && (
          <>
            <Row className="g-4">
              <Col xs={12} md={6} lg={3}>
                <div className="ca-kpi ca-kpi-cyan">
                  <span className="ca-kpi-label">Versión</span>
                  <b className="ca-kpi-value">{info.version}</b>
                  <span className="ca-kpi-note">{info.app}</span>
                </div>
              </Col>
              <Col xs={12} md={6} lg={3}>
                <div className="ca-kpi ca-kpi-green">
                  <span className="ca-kpi-label">Usuarios</span>
                  <b className="ca-kpi-value">{info.users_total}</b>
                  <span className="ca-kpi-note">
                    {info.users_hashed} con contraseña cifrada
                  </span>
                </div>
              </Col>
              <Col xs={12} md={6} lg={3}>
                <div className="ca-kpi ca-kpi-yellow">
                  <span className="ca-kpi-label">Caducidad del token</span>
                  <b className="ca-kpi-value">{info.access_token_expire_minutes} min</b>
                  <span className="ca-kpi-note">
                    JWT {info.token_algorithm} · sin renovación automática
                  </span>
                </div>
              </Col>
              <Col xs={12} md={6} lg={3}>
                <div className={`ca-kpi ${info.secret_key_configured ? "ca-kpi-green" : "ca-kpi-danger"}`}>
                  <span className="ca-kpi-label">SECRET_KEY</span>
                  <b className="ca-kpi-value">
                    {info.secret_key_configured ? "Configurada" : "Por defecto"}
                  </b>
                  <span className="ca-kpi-note">
                    {info.secret_key_configured ? "ajena al código" : "defínela en producción"}
                  </span>
                </div>
              </Col>
            </Row>

            <Row className="g-4 mt-1">
              <Col xs={12}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Tecnologías usadas</h3>
                    <Row className="g-4">
                      {TECH_GROUPS.map((group) => {
                        const items = techs.filter((t) => t.group === group);
                        if (!items.length) return null;
                        return (
                          <Col xs={12} md={6} lg={3} key={group}>
                            <h4 className="ca-tech-group-title">{group}</h4>
                            <ul className="ca-tech-list">
                              {items.map((t) => (
                                <li key={t.name}>
                                  <span className="ca-tech-name">
                                    {t.name}
                                    {t.version && <b className="ca-tech-version">{t.version}</b>}
                                  </span>
                                  {t.purpose && (
                                    <span className="ca-tech-purpose">{t.purpose}</span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          </Col>
                        );
                      })}
                    </Row>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Row className="g-4 mt-1">
              <Col xs={12} lg={6}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Base de datos</h3>
                    <p className="ca-mono">{info.database}</p>
                    <ul className="ca-role-list">
                      {Object.entries(info.tables).map(([table, count]) => (
                        <li key={table}>
                          <span>{table}</span>
                          <b>{count}</b>
                        </li>
                      ))}
                    </ul>
                  </Card.Body>
                </Card>
              </Col>

              <Col xs={12} lg={6}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Seguridad</h3>
                    <ul className="ca-check-list">
                      <li className={allHashed ? "ok" : "warn"}>
                        {allHashed
                          ? "Todas las contraseñas están cifradas con bcrypt."
                          : "Hay contraseñas sin cifrar: revisa la base de datos."}
                      </li>
                      <li className={info.secret_key_configured ? "ok" : "warn"}>
                        {info.secret_key_configured
                          ? "SECRET_KEY definida por variable de entorno."
                          : "SECRET_KEY por defecto: cámbiala antes de producción."}
                      </li>
                      <li className="ok">Contraseñas hasheadas con {info.password_hashing} (nunca en claro).</li>
                    </ul>

                    <h3 className="ca-card-title mt-4">Documentación</h3>
                    <div className="ca-form-actions">
                      <a className="ca-btn ca-btn-outline ca-btn-sm" href={info.docs} target="_blank" rel="noreferrer">
                        Swagger
                      </a>
                      <a className="ca-btn ca-btn-outline ca-btn-sm" href={info.redoc} target="_blank" rel="noreferrer">
                        ReDoc
                      </a>
                      <a className="ca-btn ca-btn-outline ca-btn-sm" href={info.openapi} target="_blank" rel="noreferrer">
                        OpenAPI
                      </a>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </>
        )}
      </Container>
    </section>
  );
}
