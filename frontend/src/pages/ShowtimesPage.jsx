import { useCallback, useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";

import { api } from "../api/client";
import { onDataChanged } from "../lib/bus";
import SectionHeader from "../components/SectionHeader";
import ShowtimeRow from "../components/ShowtimeRow";
import PaginationBar from "../components/PaginationBar";
import { useUI } from "../context/UIContext";

const PAGE_SIZE = 6;

export default function ShowtimesPage() {
  const { openBooking } = useUI();
  const [page, setPage] = useState(1);
  const [movieFilter, setMovieFilter] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [movieOptions, setMovieOptions] = useState([]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const query = `/showtimes?page=${page}&size=${PAGE_SIZE}${movieFilter ? `&movie_id=${movieFilter}` : ""}`;
    return api(query)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page, movieFilter]);

  useEffect(() => {
    load();
  }, [load]);

  // Opciones del filtro (películas que tienen funciones).
  useEffect(() => {
    let active = true;
    api("/showtimes?page=1&size=100")
      .then((d) => {
        if (!active) return;
        const seen = new Map();
        d.items.forEach((s) => s.movie && seen.set(s.movie.id, s.movie.title));
        setMovieOptions([...seen.entries()]);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  // Recarga al confirmarse una compra.
  useEffect(() => onDataChanged(load), [load]);

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="HORARIOS Y SALAS"
          title="Todas las funciones"
          sub="Filtra por película si buscas algo concreto."
        />

        <Row className="justify-content-center mb-4">
          <Col xs={12} sm={8} md={5} lg={4}>
            <Form.Group controlId="filter-movie">
              <Form.Label className="ca-field-label">Película</Form.Label>
              <Form.Select
                value={movieFilter}
                onChange={(e) => {
                  setMovieFilter(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todas</option>
                {movieOptions.map(([id, title]) => (
                  <option key={id} value={id}>
                    {title}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
        </Row>

        <div className="ca-showtime-list">
          {loading && <div className="ca-empty">Cargando funciones…</div>}
          {!loading && error && (
            <div className="ca-empty">No se pudieron cargar las funciones: {error}</div>
          )}
          {!loading && !error && !data?.items.length && (
            <div className="ca-empty">No hay funciones para este filtro.</div>
          )}
          {!loading &&
            !error &&
            data?.items.map((s) => (
              <ShowtimeRow key={s.id} showtime={s} movieTitle={s.movie?.title} onBook={openBooking} />
            ))}
        </div>

        <PaginationBar data={data} onChange={setPage} ariaLabel="Paginación de funciones" />
      </Container>
    </section>
  );
}
