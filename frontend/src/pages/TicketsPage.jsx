import { useCallback, useEffect, useRef, useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

import { api } from "../api/client";
import { onDataChanged } from "../lib/bus";
import { fmtDate, price } from "../lib/format";
import SectionHeader from "../components/SectionHeader";
import PaginationBar from "../components/PaginationBar";

const PAGE_SIZE = 6;

export default function TicketsPage() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const showtimesById = useRef(new Map());

  const loadShowtimes = useCallback(async () => {
    if (showtimesById.current.size) return;
    try {
      const d = await api("/showtimes?page=1&size=100");
      d.items.forEach((s) => showtimesById.current.set(s.id, s));
    } catch {
      /* silencioso: los títulos se resolverán de forma parcial */
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await loadShowtimes();
      const d = await api(`/tickets?page=${page}&size=${PAGE_SIZE}`);
      setData(d);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, loadShowtimes]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => onDataChanged(load), [load]);

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader eyebrow="TU HISTORIAL" title="Mis entradas" sub="Tus reservas confirmadas." />

        {loading && <div className="ca-empty">Cargando tus entradas…</div>}
        {!loading && error && (
          <div className="ca-empty">No se pudieron cargar tus entradas: {error}</div>
        )}
        {!loading && !error && !data?.items.length && (
          <div className="ca-empty">Todavía no has comprado ninguna entrada.</div>
        )}

        {!loading && !error && !!data?.items.length && (
          <Row className="g-3">
            {data.items.map((t) => {
              const st = showtimesById.current.get(t.showtime_id);
              const title = st?.movie ? st.movie.title : `Función #${t.showtime_id}`;
              const when = st ? fmtDate(st.start_time).full : "";
              const seats = t.seats?.length ? [...t.seats].sort().join(", ") : "";
              return (
                <Col xs={12} lg={6} key={t.id}>
                  <div className="ca-ticket">
                    <div>
                      <p className="ca-eyebrow mb-1">◆ ENTRADA #{t.id} ◆</p>
                      <h4>{title}</h4>
                      <div className="ca-ticket-meta">
                        {st?.room || ""}
                        {when ? ` · ${when}` : ""}
                      </div>
                      <div className="ca-ticket-meta">
                        {t.quantity} × entrada{seats ? ` · Butacas: ${seats}` : ""} · a nombre de{" "}
                        {t.customer_name}
                      </div>
                    </div>
                    <div className="ca-ticket-total">{price(t.total_price)}</div>
                  </div>
                </Col>
              );
            })}
          </Row>
        )}

        <PaginationBar data={data} onChange={setPage} ariaLabel="Paginación de entradas" />
      </Container>
    </section>
  );
}
