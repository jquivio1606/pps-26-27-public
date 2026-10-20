import { useEffect } from "react";
import Form from "react-bootstrap/Form";

/**
 * Paginador compacto para tablas: « 1/3 » + selector de filas por página.
 * Pinta una sola línea para no ocupar media pantalla.
 */
export default function TablePager({
  page,
  setPage,
  size,
  setSize,
  total,
  sizes = [5, 10],
  ariaLabel = "Paginación",
}) {
  const pages = Math.max(1, Math.ceil(total / size));

  // Si al borrar/filtrar la página actual se queda fuera de rango, la recolocamos.
  useEffect(() => {
    if (page > pages) setPage(pages);
  }, [page, pages, setPage]);

  const safePage = Math.min(page, pages);
  const from = total === 0 ? 0 : (safePage - 1) * size + 1;
  const to = Math.min(safePage * size, total);

  return (
    <nav className="ca-table-pager" aria-label={ariaLabel}>
      <span className="ca-pager-info">
        {from}–{to} de {total}
      </span>

      <div className="ca-pager-controls">
        <Form.Select
          size="sm"
          className="ca-pager-size"
          value={size}
          onChange={(e) => {
            setSize(Number(e.target.value));
            setPage(1);
          }}
          aria-label="Filas por página"
        >
          {sizes.map((s) => (
            <option key={s} value={s}>
              {s} / pág.
            </option>
          ))}
        </Form.Select>

        <button
          type="button"
          className="ca-btn ca-btn-ghost ca-btn-sm ca-pager-btn"
          disabled={safePage <= 1}
          onClick={() => setPage(safePage - 1)}
          aria-label="Página anterior"
        >
          ‹
        </button>
        <span className="ca-pager-page">
          {safePage}/{pages}
        </span>
        <button
          type="button"
          className="ca-btn ca-btn-ghost ca-btn-sm ca-pager-btn"
          disabled={safePage >= pages}
          onClick={() => setPage(safePage + 1)}
          aria-label="Página siguiente"
        >
          ›
        </button>
      </div>
    </nav>
  );
}
