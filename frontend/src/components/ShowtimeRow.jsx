import { fmtDate, price } from "../lib/format";

function SeatPill({ available, total }) {
  const ratio = total ? available / total : 0;
  if (available <= 0) return <span className="ca-pill ca-pill-out">Agotada</span>;
  if (ratio <= 0.2) return <span className="ca-pill ca-pill-low">Últimas {available}</span>;
  return <span className="ca-pill ca-pill-ok">{available} disponibles</span>;
}

export default function ShowtimeRow({ showtime, movieTitle, onBook, compact = false }) {
  const f = fmtDate(showtime.start_time);
  const title = movieTitle || showtime.movie?.title || `Función #${showtime.id}`;
  const soldOut = showtime.available_seats <= 0;

  return (
    <div className={`ca-showtime${compact ? " ca-showtime-compact" : ""}`}>
      <div className="ca-showtime-date">
        <span className="d">{f.day}</span>
        <span className="m">
          {f.month} · {f.time}
        </span>
      </div>

      <div className="ca-showtime-info">
        <h4>{title}</h4>
        <div className="ca-showtime-meta">
          <span>🏛️ {showtime.room}</span>
          <span>👥 Aforo {showtime.total_seats}</span>
          <SeatPill available={showtime.available_seats} total={showtime.total_seats} />
        </div>
      </div>

      <div className="ca-showtime-action">
        <span className="ca-showtime-price">{price(showtime.price)}</span>
        <button
          type="button"
          className="ca-btn ca-btn-primary ca-btn-sm"
          disabled={soldOut}
          onClick={() => onBook(showtime.id)}
        >
          {soldOut ? "Agotada" : "Comprar"}
        </button>
      </div>
    </div>
  );
}
