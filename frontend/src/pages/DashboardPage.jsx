import { useCallback, useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Card from "react-bootstrap/Card";
import Table from "react-bootstrap/Table";

import { api } from "../api/client";
import { onDataChanged } from "../lib/bus";
import { price, roleLabel } from "../lib/format";
import SectionHeader from "../components/SectionHeader";

const KPI = [
  { key: "revenue", label: "Ingresos", format: (v) => price(v), accent: "pink" },
  { key: "seats_sold", label: "Entradas vendidas", accent: "cyan" },
  { key: "tickets", label: "Reservas", accent: "yellow" },
  { key: "users", label: "Usuarios", accent: "green" },
  { key: "movies", label: "Películas" },
  { key: "showtimes", label: "Funciones" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStats(await api("/stats/dashboard"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => onDataChanged(load), [load]);

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="PANEL DE DIRECCIÓN"
          title="Dashboard"
          sub="Estadísticas en vivo de la web: ventas, ocupación y usuarios."
        />

        {loading && <div className="ca-empty">Calculando estadísticas…</div>}
        {!loading && error && (
          <div className="ca-empty">No se pudieron cargar las estadísticas: {error}</div>
        )}

        {!loading && !error && stats && (
          <>
            <div className="ca-kpis">
              {KPI.map((kpi) => (
                <div className={`ca-kpi ca-kpi-${kpi.accent || "base"}`} key={kpi.key}>
                  <span className="ca-kpi-label">{kpi.label}</span>
                  <b className="ca-kpi-value">
                    {kpi.format ? kpi.format(stats[kpi.key]) : stats[kpi.key]}
                  </b>
                </div>
              ))}
            </div>

            <Row className="g-4 mt-1">
              <Col xs={12} lg={5}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Ocupación de las salas</h3>
                    <div className="ca-bar">
                      <div
                        className="ca-bar-fill"
                        style={{ width: `${Math.min(stats.occupancy_percent, 100)}%` }}
                      />
                    </div>
                    <p className="ca-kpi-note">
                      {stats.occupancy_percent}% ocupado · {stats.seats_reserved} butacas vendidas de{" "}
                      {stats.seats_total} ({stats.seats_available} libres)
                    </p>

                    <h3 className="ca-card-title mt-4">Usuarios por rol</h3>
                    <ul className="ca-role-list">
                      {Object.entries(stats.users_by_role).map(([role, count]) => (
                        <li key={role}>
                          <span>{roleLabel(role)}</span>
                          <b>{count}</b>
                        </li>
                      ))}
                    </ul>
                  </Card.Body>
                </Card>
              </Col>

              <Col xs={12} lg={7}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Películas más taquilleras</h3>
                    <div className="ca-table-wrap">
                      <Table responsive borderless className="ca-table align-middle">
                        <thead>
                          <tr>
                            <th>Película</th>
                            <th className="text-end">Funciones</th>
                            <th className="text-end">Entradas</th>
                            <th className="text-end">Ingresos</th>
                          </tr>
                        </thead>
                        <tbody>
                          {stats.top_movies.map((movie) => (
                            <tr key={movie.movie_id}>
                              <td>{movie.title}</td>
                              <td className="text-end">{movie.showtimes}</td>
                              <td className="text-end">{movie.seats_sold}</td>
                              <td className="text-end">{price(movie.revenue)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Row className="g-4 mt-1">
              <Col xs={12}>
                <Card className="ca-card">
                  <Card.Body>
                    <h3 className="ca-card-title">Últimas reservas</h3>
                    {stats.recent_tickets.length === 0 ? (
                      <p className="ca-kpi-note">Todavía no hay reservas registradas.</p>
                    ) : (
                      <div className="ca-table-wrap">
                        <Table responsive borderless className="ca-table align-middle">
                          <thead>
                            <tr>
                              <th>#</th>
                              <th>Cliente</th>
                              <th>Función</th>
                              <th className="text-end">Entradas</th>
                              <th className="text-end">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {stats.recent_tickets.map((ticket) => (
                              <tr key={ticket.id}>
                                <td>{ticket.id}</td>
                                <td>{ticket.customer_name}</td>
                                <td>{ticket.showtime_id}</td>
                                <td className="text-end">{ticket.quantity}</td>
                                <td className="text-end">{price(ticket.total_price)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </div>
                    )}
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
