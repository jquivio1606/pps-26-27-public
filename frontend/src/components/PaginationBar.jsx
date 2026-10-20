/**
 * Paginación con botones Anterior/Siguiente y números con elipsis.
 * `data` es el envoltorio `Page` que devuelve la API.
 */
export default function PaginationBar({ data, onChange, ariaLabel = "Paginación" }) {
  if (!data || !data.pages || data.pages <= 1) return null;

  const current = data.page;

  const pages = [];
  for (let p = 1; p <= data.pages; p++) {
    if (p === 1 || p === data.pages || Math.abs(p - current) <= 1) pages.push(p);
    else if (pages[pages.length - 1] !== "…") pages.push("…");
  }

  return (
    <nav className="ca-pagination" aria-label={ariaLabel}>
      <button type="button" disabled={!data.has_prev} onClick={() => onChange(current - 1)}>
        « Anterior
      </button>

      {pages.map((p, i) =>
        p === "…" ? (
          <span key={`gap-${i}`} className="ca-page-info">
            …
          </span>
        ) : (
          <button
            key={p}
            type="button"
            className={p === current ? "active" : ""}
            aria-current={p === current ? "page" : undefined}
            onClick={() => onChange(p)}
          >
            {p}
          </button>
        )
      )}

      <button type="button" disabled={!data.has_next} onClick={() => onChange(current + 1)}>
        Siguiente »
      </button>
    </nav>
  );
}
