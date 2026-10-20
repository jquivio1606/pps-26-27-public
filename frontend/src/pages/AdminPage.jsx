import { useCallback, useEffect, useMemo, useState } from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Card from "react-bootstrap/Card";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";

import { api } from "../api/client";
import { emitDataChanged } from "../lib/bus";
import { fmtDate, price } from "../lib/format";
import SectionHeader from "../components/SectionHeader";
import AdminTabs from "../components/AdminTabs";
import TablePager from "../components/TablePager";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

const EMPTY_MOVIE = { title: "", genre: "", duration_minutes: "", poster_url: "" };
const EMPTY_SHOWTIME = { movie_id: "", room: "", start_time: "", total_seats: "", price: "8" };

/** Convierte un ISO de la API al formato que espera <input type="datetime-local">. */
const toLocalInput = (iso) => (iso ? String(iso).slice(0, 16) : "");

export default function AdminPage() {
  const toast = useToast();
  const { user } = useAuth();
  const [movies, setMovies] = useState([]);
  const [showtimes, setShowtimes] = useState([]);
  const [movieForm, setMovieForm] = useState(EMPTY_MOVIE);
  const [showtimeForm, setShowtimeForm] = useState(EMPTY_SHOWTIME);
  const [editingMovieId, setEditingMovieId] = useState(null);
  const [editingShowtimeId, setEditingShowtimeId] = useState(null);
  const [moviePage, setMoviePage] = useState(1);
  const [movieSize, setMovieSize] = useState(5);
  const [showtimePage, setShowtimePage] = useState(1);
  const [showtimeSize, setShowtimeSize] = useState(5);

  const loadCatalog = useCallback(async () => {
    try {
      const [moviesData, showtimesData] = await Promise.all([
        api("/movies?page=1&size=100"),
        api("/showtimes?page=1&size=100"),
      ]);
      setMovies(moviesData.items);
      setShowtimes(showtimesData.items);
    } catch (err) {
      toast.push("No se pudo cargar el catálogo", err.message, "error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  // ----------------------------- Películas ------------------------------- //
  const submitMovie = async (e) => {
    e.preventDefault();
    const body = {
      title: movieForm.title,
      genre: movieForm.genre,
      duration_minutes: Number(movieForm.duration_minutes),
      poster_url: movieForm.poster_url.trim() || null,
    };
    try {
      if (editingMovieId) {
        await api(`/movies/${editingMovieId}`, { method: "PUT", body });
        toast.push("Película actualizada", body.title, "success");
      } else {
        await api("/movies", { method: "POST", body });
        toast.push("Película creada", body.title, "success");
      }
      setMovieForm(EMPTY_MOVIE);
      setEditingMovieId(null);
      await loadCatalog();
      emitDataChanged();
    } catch (err) {
      toast.push("No se pudo guardar la película", err.message, "error");
    }
  };

  const editMovie = (movie) => {
    setEditingMovieId(movie.id);
    setMovieForm({
      title: movie.title,
      genre: movie.genre,
      duration_minutes: String(movie.duration_minutes),
      poster_url: movie.poster_url || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteMovie = async (movie) => {
    if (!window.confirm(`¿Eliminar la película "${movie.title}" y sus funciones?`)) return;
    try {
      await api(`/movies/${movie.id}`, { method: "DELETE" });
      toast.push("Película eliminada", movie.title, "success");
      if (editingMovieId === movie.id) {
        setEditingMovieId(null);
        setMovieForm(EMPTY_MOVIE);
      }
      await loadCatalog();
      emitDataChanged();
    } catch (err) {
      toast.push("No se pudo eliminar la película", err.message, "error");
    }
  };

  // ----------------------------- Funciones ------------------------------- //
  const submitShowtime = async (e) => {
    e.preventDefault();
    const body = {
      movie_id: Number(showtimeForm.movie_id),
      room: showtimeForm.room,
      start_time: showtimeForm.start_time,
      total_seats: Number(showtimeForm.total_seats),
      price: Number(showtimeForm.price || 0),
    };
    try {
      if (editingShowtimeId) {
        await api(`/showtimes/${editingShowtimeId}`, { method: "PUT", body });
        toast.push("Función actualizada", body.room, "success");
      } else {
        await api("/showtimes", { method: "POST", body });
        toast.push("Función creada", body.room, "success");
      }
      setShowtimeForm(EMPTY_SHOWTIME);
      setEditingShowtimeId(null);
      await loadCatalog();
      emitDataChanged();
    } catch (err) {
      toast.push("No se pudo guardar la función", err.message, "error");
    }
  };

  const editShowtime = (showtime) => {
    setEditingShowtimeId(showtime.id);
    setShowtimeForm({
      movie_id: String(showtime.movie_id),
      room: showtime.room,
      start_time: toLocalInput(showtime.start_time),
      total_seats: String(showtime.total_seats),
      price: String(showtime.price ?? 0),
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteShowtime = async (showtime) => {
    if (!window.confirm(`¿Eliminar la función de la ${showtime.room}?`)) return;
    try {
      await api(`/showtimes/${showtime.id}`, { method: "DELETE" });
      toast.push("Función eliminada", showtime.room, "success");
      if (editingShowtimeId === showtime.id) {
        setEditingShowtimeId(null);
        setShowtimeForm(EMPTY_SHOWTIME);
      }
      await loadCatalog();
      emitDataChanged();
    } catch (err) {
      toast.push("No se pudo eliminar la función", err.message, "error");
    }
  };

  const movieById = (id) => movies.find((m) => m.id === Number(id));

  // Trozos visibles según la página activa (paginación en cliente).
  const visibleMovies = useMemo(() => {
    const start = (moviePage - 1) * movieSize;
    return movies.slice(start, start + movieSize);
  }, [movies, moviePage, movieSize]);

  const visibleShowtimes = useMemo(() => {
    const start = (showtimePage - 1) * showtimeSize;
    return showtimes.slice(start, start + showtimeSize);
  }, [showtimes, showtimePage, showtimeSize]);

  const setM = (key) => (e) => setMovieForm((f) => ({ ...f, [key]: e.target.value }));
  const setS = (key) => (e) => setShowtimeForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="ZONA DE GESTIÓN"
          title="Catálogo"
          sub={
            user?.role === "manager"
              ? "Como jefe puedes añadir, modificar y eliminar películas y funciones."
              : "Añade, modifica y elimina películas y funciones de la cartelera."
          }
        />
        <AdminTabs />

        <Row className="g-4">
          <Col xs={12} lg={6}>
            <Card className="ca-card">
              <Card.Body>
                <h3 className="ca-card-title">
                  {editingMovieId ? `Editar película #${editingMovieId}` : "Nueva película"}
                </h3>
                <Form onSubmit={submitMovie}>
                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Título</Form.Label>
                    <Form.Control
                      required
                      minLength={1}
                      maxLength={200}
                      value={movieForm.title}
                      onChange={setM("title")}
                      placeholder="Ej. Origen"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Género</Form.Label>
                    <Form.Control
                      required
                      maxLength={100}
                      value={movieForm.genre}
                      onChange={setM("genre")}
                      placeholder="Ej. Ciencia ficción"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Duración (min)</Form.Label>
                    <Form.Control
                      type="number"
                      min={1}
                      required
                      value={movieForm.duration_minutes}
                      onChange={setM("duration_minutes")}
                      placeholder="148"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">URL del póster (opcional)</Form.Label>
                    <Form.Control
                      type="url"
                      maxLength={500}
                      value={movieForm.poster_url}
                      onChange={setM("poster_url")}
                      placeholder="https://…/poster.jpg"
                    />
                  </Form.Group>

                  <div className="ca-form-actions">
                    <button type="submit" className="ca-btn ca-btn-primary">
                      {editingMovieId ? "Guardar cambios" : "Crear película"}
                    </button>
                    {editingMovieId && (
                      <button
                        type="button"
                        className="ca-btn ca-btn-ghost"
                        onClick={() => {
                          setEditingMovieId(null);
                          setMovieForm(EMPTY_MOVIE);
                        }}
                      >
                        Cancelar
                      </button>
                    )}
                  </div>
                </Form>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} lg={6}>
            <Card className="ca-card">
              <Card.Body>
                <h3 className="ca-card-title">
                  {editingShowtimeId ? `Editar función #${editingShowtimeId}` : "Nueva función"}
                </h3>
                <Form onSubmit={submitShowtime}>
                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Película</Form.Label>
                    <Form.Select required value={showtimeForm.movie_id} onChange={setS("movie_id")}>
                      <option value="">Selecciona una película</option>
                      {movies.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.title}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Sala</Form.Label>
                    <Form.Control
                      required
                      maxLength={50}
                      value={showtimeForm.room}
                      onChange={setS("room")}
                      placeholder="Ej. Sala 1"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label className="ca-field-label">Fecha y hora</Form.Label>
                    <Form.Control
                      type="datetime-local"
                      required
                      value={showtimeForm.start_time}
                      onChange={setS("start_time")}
                    />
                  </Form.Group>

                  <Row className="g-3 mb-3">
                    <Col xs={12} sm={6}>
                      <Form.Group>
                        <Form.Label className="ca-field-label">Asientos totales</Form.Label>
                        <Form.Control
                          type="number"
                          min={1}
                          required
                          value={showtimeForm.total_seats}
                          onChange={setS("total_seats")}
                          placeholder="100"
                        />
                      </Form.Group>
                    </Col>
                    <Col xs={12} sm={6}>
                      <Form.Group>
                        <Form.Label className="ca-field-label">Precio (€)</Form.Label>
                        <Form.Control
                          type="number"
                          min={0}
                          step={0.5}
                          value={showtimeForm.price}
                          onChange={setS("price")}
                        />
                      </Form.Group>
                    </Col>
                  </Row>

                  <div className="ca-form-actions">
                    <button type="submit" className="ca-btn ca-btn-primary">
                      {editingShowtimeId ? "Guardar cambios" : "Crear función"}
                    </button>
                    {editingShowtimeId && (
                      <button
                        type="button"
                        className="ca-btn ca-btn-ghost"
                        onClick={() => {
                          setEditingShowtimeId(null);
                          setShowtimeForm(EMPTY_SHOWTIME);
                        }}
                      >
                        Cancelar
                      </button>
                    )}
                  </div>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row className="g-4 mt-1">
          <Col xs={12} lg={6}>
            <Card className="ca-card">
              <Card.Body>
                <h3 className="ca-card-title">Películas ({movies.length})</h3>
                <div className="ca-table-wrap">
                  <Table responsive borderless className="ca-table align-middle">
                    <thead>
                      <tr>
                        <th>Título</th>
                        <th>Género</th>
                        <th className="text-end">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleMovies.map((movie) => (
                        <tr key={movie.id}>
                          <td>
                            #{movie.id} · {movie.title}
                          </td>
                          <td>{movie.genre}</td>
                          <td className="text-end ca-row-actions">
                            <button
                              type="button"
                              className="ca-btn ca-btn-outline ca-btn-sm"
                              onClick={() => editMovie(movie)}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="ca-btn ca-btn-ghost ca-btn-sm"
                              onClick={() => deleteMovie(movie)}
                            >
                              Eliminar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
                <TablePager
                  page={moviePage}
                  setPage={setMoviePage}
                  size={movieSize}
                  setSize={setMovieSize}
                  total={movies.length}
                  ariaLabel="Paginación de películas"
                />
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} lg={6}>
            <Card className="ca-card">
              <Card.Body>
                <h3 className="ca-card-title">Funciones ({showtimes.length})</h3>
                <div className="ca-table-wrap">
                  <Table responsive borderless className="ca-table align-middle">
                    <thead>
                      <tr>
                        <th>Película / Sala</th>
                        <th>Cuando</th>
                        <th className="text-end">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleShowtimes.map((showtime) => {
                        const movie = movieById(showtime.movie_id) || showtime.movie;
                        return (
                          <tr key={showtime.id}>
                            <td>
                              #{showtime.id} · {movie?.title || `Película ${showtime.movie_id}`}
                              <div className="ca-table-sub">
                                {showtime.room} · {showtime.available_seats}/{showtime.total_seats}{" "}
                                libres · {price(showtime.price)}
                              </div>
                            </td>
                            <td>{fmtDate(showtime.start_time).full}</td>
                            <td className="text-end ca-row-actions">
                              <button
                                type="button"
                                className="ca-btn ca-btn-outline ca-btn-sm"
                                onClick={() => editShowtime(showtime)}
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                className="ca-btn ca-btn-ghost ca-btn-sm"
                                onClick={() => deleteShowtime(showtime)}
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
                <TablePager
                  page={showtimePage}
                  setPage={setShowtimePage}
                  size={showtimeSize}
                  setSize={setShowtimeSize}
                  total={showtimes.length}
                  ariaLabel="Paginación de funciones"
                />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </section>
  );
}
