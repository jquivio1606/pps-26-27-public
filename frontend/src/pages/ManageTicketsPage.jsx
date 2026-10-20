import { useCallback, useEffect, useState } from "react";
import Container from "react-bootstrap/Container";
import Card from "react-bootstrap/Card";
import Form from "react-bootstrap/Form";
import Table from "react-bootstrap/Table";

import { api } from "../api/client";
import { emitDataChanged } from "../lib/bus";
import { fmtDate, price } from "../lib/format";
import SectionHeader from "../components/SectionHeader";
import AdminTabs from "../components/AdminTabs";
import PaginationBar from "../components/PaginationBar";
import { useToast } from "../context/ToastContext";

const PAGE_SIZE = 10;

/**
 * Pestaña «Entradas» de la gestión (manager y admin).
 *
 * Lista **todas** las reservas de la web (``?scope=all``) con un filtro por
 * cliente o usuario, y permite cancelar una entrada cuando el cliente se ha
 * equivocado al comprarla: las butacas vuelven a estar libres al instante.
 * El reembolso del dinero queda fuera de la web (no hay pasarela de pago).
 */
export default function ManageTicketsPage() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const query = search.trim();
      const url =
        `/tickets?scope=all&page=${page}&size=${PAGE_SIZE}` +
        (query ? `&search=${encodeURIComponent(query)}` : "");
      const d = await api(url);
      // Si la página quedó vacía (p. ej. al cancelar la última de la lista),
      // volvemos a la primera para no dejar una tabla colgada.
      if (!d.items.length && d.total > 0 && page > 1) {
        setPage(1);
        return;
      }
      setData(d);
    } catch (err) {
      setError(err.message);
    }
  }, [page, search]);

  useEffect(() => {
    load();
  }, [load]);

  const applySearch = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const clearSearch = () => {
    setSearchInput("");
    setSearch("");
    setPage(1);
  };

  const cancelTicket = async (t) => {
    const message =
      `¿Cancelar la entrada #${t.id} de "${t.customer_name}"?\n\n` +
      `Se liberarán ${t.quantity} butaca(s) y la reserva dejará de contar en las estadísticas.\n\n` +
      "Atención: el reembolso del dinero NO se realiza en la web " +
      "(no hay pasarela de pago): devuélvelo fuera de la plataforma.";
    if (!window.confirm(message)) return;

    setBusyId(t.id);
    try {
      await api(`/tickets/${t.id}`, { method: "DELETE" });
      toast.push(
        "Entrada cancelada",
        `#${t.id} · ${t.customer_name} · ${t.quantity} butaca(s) liberadas.`,
        "success",
      );
      emitDataChanged();
      await load();
    } catch (err) {
      toast.push("No se pudo cancelar la entrada", err.message, "error");
      await load();
    } finally {
      setBusyId(null);
    }
  };

  const emptyText = search.trim()
    ? `No hay entradas que coincidan con «${search.trim()}».`
    : "Todavía no hay entradas de reserva.";

  return (
    <section className="ca-section ca-section-first">
      <Container>
        <SectionHeader
          eyebrow="ZONA DE GESTIÓN"
          title="Entradas"
          sub="Busca la entrada de un cliente y cancélala si se equivocó al comprar: las butacas quedan libres al instante."
        />
        <AdminTabs />

        {error && <div className="ca-empty">No se pudieron cargar las entradas: {error}</div>}

        <Form className="d-flex gap-2 mb-3" role="search" onSubmit={applySearch}>
          <Form.Control
            type="search"
            className="flex-grow-1"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Filtrar por cliente o usuario…"
            aria-label="Filtrar entradas por cliente o usuario"
          />
          <button type="submit" className="ca-btn ca-btn-outline">
            Buscar
          </button>
          {search && (
            <button type="button" className="ca-btn ca-btn-ghost" onClick={clearSearch}>
              Limpiar
            </button>
          )}
        </Form>

        <Card className="ca-card">
          <Card.Body>
            <p className="ca-kpi-note">
              La cancelación libera las butacas y descuenta la venta de las
              estadísticas. <b>El reembolso del dinero se hace fuera de la web</b>{" "}
              (el pago tampoco está integrado).
            </p>

            <div className="ca-table-wrap">
              <Table responsive borderless className="ca-table align-middle">
                <thead>
                  <tr>
                    <th>Entrada</th>
                    <th>Comprador</th>
                    <th>Función</th>
                    <th>Butacas</th>
                    <th className="text-end">Importe</th>
                    <th className="text-end">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.items || []).map((t) => (
                    <tr key={t.id}>
                      <td>#{t.id}</td>
                      <td>
                        {t.customer_name}
                        <span className="ca-table-sub">
                          {t.username ? ` · @${t.username}` : " · sin cuenta vinculada"}
                        </span>
                      </td>
                      <td>
                        {t.movie_title || `Función #${t.showtime_id}`}
                        <span className="ca-table-sub">
                          {t.room ? ` · ${t.room}` : ""}
                          {t.start_time ? ` · ${fmtDate(t.start_time).full}` : ""}
                        </span>
                      </td>
                      <td>
                        {t.quantity} entrada{t.quantity > 1 ? "s" : ""}
                        {t.seats?.length ? (
                          <span className="ca-table-sub"> · {t.seats.join(", ")}</span>
                        ) : null}
                      </td>
                      <td className="text-end">{price(t.total_price)}</td>
                      <td className="text-end ca-row-actions">
                        <button
                          type="button"
                          className="ca-btn ca-btn-ghost ca-btn-sm"
                          onClick={() => cancelTicket(t)}
                          disabled={busyId === t.id}
                          title="Cancelar esta entrada y liberar sus butacas"
                        >
                          {busyId === t.id ? "Cancelando…" : "Cancelar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            {data && !data.items.length && <div className="ca-empty">{emptyText}</div>}

            <PaginationBar data={data} onChange={setPage} ariaLabel="Paginación de entradas" />
          </Card.Body>
        </Card>
      </Container>
    </section>
  );
}
