import { useState } from "react";

import { genreEmoji, posterStyle } from "../lib/format";

export default function MovieCard({ movie, onOpen }) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImg = movie.poster_url && !imgFailed;

  const handleKey = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onOpen(movie.id);
    }
  };

  return (
    <article
      className="ca-movie-card"
      tabIndex={0}
      role="button"
      aria-label={movie.title}
      onClick={() => onOpen(movie.id)}
      onKeyDown={handleKey}
    >
      <div className="ca-poster" style={posterStyle(movie)}>
        {showImg && (
          <img
            className="ca-poster-img"
            src={movie.poster_url}
            alt={`Póster de ${movie.title}`}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImgFailed(true)}
          />
        )}
        <span className="ca-poster-genre">{movie.genre}</span>
        <span className="ca-poster-emoji">{genreEmoji(movie.genre)}</span>
        <span className="ca-poster-duration">{movie.duration_minutes} min</span>
      </div>

      <div className="ca-movie-card-body">
        <h3 className="ca-movie-card-title">{movie.title}</h3>
        <span className="ca-movie-card-cta">Ver funciones →</span>
      </div>
    </article>
  );
}
