import { useEffect, useState } from "react";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";

import { api } from "../api/client";
import { genreEmoji, posterStyle } from "../lib/format";
import ShowtimeRow from "./ShowtimeRow";
import { useUI } from "../context/UIContext";

export default function MovieModal() {
  const { movieId, closeMovie, openBooking } = useUI();
  const [state, setState] = useState({ loading: false, error: null, movie: null, showtimes: [] });

  useEffect(() => {
    if (movieId == null) return;
    let active = true;
    setState({ loading: true, error: null, movie: null, showtimes: [] });

    Promise.all([
      api(`/movies/${movieId}`),
      api(`/showtimes?movie_id=${movieId}&size=100`),
    ])
      .then(([movie, showtimes]) => {
        if (active) setState({ loading: false, error: null, movie, showtimes: showtimes.items });
      })
      .catch((err) => {
        if (active) setState({ loading: false, error: err.message, movie: null, showtimes: [] });
      });

    return () => {
      active = false;
    };
  }, [movieId]);

  const { loading, error, movie, showtimes } = state;

  return (
    <Modal show={movieId != null} onHide={closeMovie} size="xl" centered scrollable className="ca-modal">
      <Modal.Body>
        {loading && (
          <div className="ca-loading">
            <Spinner animation="border" />
            <span>Cargando ficha…</span>
          </div>
        )}

        {error && <div className="ca-empty">No se pudo cargar la película: {error}</div>}

        {movie && (
          <div className="ca-movie-detail">
            <div className="ca-poster" style={posterStyle(movie)}>
              {movie.poster_url && (
                <img
                  className="ca-poster-img"
                  src={movie.poster_url}
                  alt={`Póster de ${movie.title}`}
                  referrerPolicy="no-referrer"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              )}
              <span className="ca-poster-emoji">{genreEmoji(movie.genre)}</span>
            </div>

            <div className="ca-movie-detail-body">
              <p className="ca-eyebrow">◆ FICHA ◆</p>
              <h2>{movie.title}</h2>
              <div className="ca-movie-tags">
                <span className="ca-pill">{movie.genre}</span>
                <span className="ca-pill">{movie.duration_minutes} min</span>
                <span className="ca-pill">{showtimes.length} funciones</span>
              </div>

              <div className="ca-showtime-list">
                {showtimes.length ? (
                  showtimes.map((s) => (
                    <ShowtimeRow key={s.id} showtime={s} movieTitle={movie.title} onBook={openBooking} compact />
                  ))
                ) : (
                  <div className="ca-empty">No hay funciones programadas para esta película.</div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal.Body>
    </Modal>
  );
}
