import { useEffect, useMemo, useState } from "react";
import Modal from "react-bootstrap/Modal";
import Form from "react-bootstrap/Form";
import Spinner from "react-bootstrap/Spinner";

import { api } from "../api/client";
import { emitDataChanged } from "../lib/bus";
import { fmtDate, price } from "../lib/format";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useUI } from "../context/UIContext";
import SeatMap from "./SeatMap";

export default function BookingModal() {
  const { bookingId, closeBooking } = useUI();
  const { user } = useAuth();
  const toast = useToast();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [seatMap, setSeatMap] = useState(null);
  const [showtime, setShowtime] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [selected, setSelected] = useState(() => new Set());
  const [customerName, setCustomerName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadSeatMap = (id) => api(`/showtimes/${id}/seats`);

  // Reinicia el estado cada vez que se abre una función distinta.
  useEffect(() => {
    if (bookingId == null) return;
    let active = true;
    setLoading(true);
    setError(null);
    setSeatMap(null);
    setShowtime(null);
    setQuantity(1);
    setSelected(new Set());
    setCustomerName(user?.username || "");
    setSubmitting(false);

    Promise.all([loadSeatMap(bookingId), api(`/showtimes/${bookingId}`)])
      .then(([seats, show]) => {
        if (!active) return;
        setSeatMap(seats);
        setShowtime(show);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookingId, user?.username]);

  const maxQty = useMemo(() => {
    if (!seatMap) return 1;
    const freeSeats = seatMap.total_seats - seatMap.reserved.length;
    return Math.max(1, Math.min(seatMap.available_seats, freeSeats));
  }, [seatMap]);

  // Al cambiar la cantidad, recorta la selección si sobra.
  useEffect(() => {
    setSelected((prev) => {
      if (prev.size <= quantity) return prev;
      const next = new Set([...prev].slice(0, quantity));
      return next;
    });
  }, [quantity]);

  const toggleSeat = (label, reserved) => {
    if (reserved) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        if (next.size >= quantity) {
          toast.push("Máximo alcanzado", `Solo puedes elegir ${quantity} butaca(s) para ${quantity} entrada(s).`);
          return prev;
        }
        next.add(label);
      }
      return next;
    });
  };

  const selectedList = useMemo(() => [...selected].sort(), [selected]);
  const ready = selectedList.length === quantity;
  const unitPrice = showtime ? Number(showtime.price || 0) : 0;

  const changeQty = (delta) => {
    setQuantity((q) => Math.max(1, Math.min(maxQty, q + delta)));
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!ready || !seatMap) return;
    setSubmitting(true);
    try {
      const result = await api("/tickets/book", {
        method: "POST",
        body: {
          showtime_id: bookingId,
          customer_name: customerName,
          quantity,
          seats: selectedList,
        },
      });
      closeBooking();
      toast.push(
        "¡Compra confirmada!",
        `Butacas ${result.ticket.seats.join(", ")} · Total ${Number(result.ticket.total_price).toFixed(2)} €`,
        "success"
      );
      emitDataChanged();
    } catch (err) {
      if (err.status === 409) {
        toast.push("Butaca ocupada", err.message, "error");
        // Recargamos el mapa de butacas, que puede haber cambiado.
        api(`/showtimes/${bookingId}/seats`)
          .then((data) => {
            setSeatMap(data);
            setSelected(new Set());
          })
          .catch(() => {});
      } else {
        toast.push("No se pudo completar", err.message, "error");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const room = seatMap?.room || "";
  const movieTitle = showtime?.movie?.title || (showtime ? `Función #${showtime.id}` : "");

  return (
    <Modal show={bookingId != null} onHide={closeBooking} size="lg" centered scrollable className="ca-modal">
      <Modal.Body>
        {loading && (
          <div className="ca-loading">
            <Spinner animation="border" />
            <span>Cargando butacas…</span>
          </div>
        )}

        {error && <div className="ca-empty">No se pudo cargar el mapa de butacas: {error}</div>}

        {seatMap && (
          <form onSubmit={submit}>
            <p className="ca-eyebrow">◆ ELIGE TUS BUTACAS ◆</p>
            {movieTitle && <h3 className="ca-booking-title">{movieTitle}</h3>}
            <p className="ca-section-sub mb-3">
              {room}
              {showtime ? ` · ${fmtDate(showtime.start_time).full}` : ""} · {price(unitPrice)}/entrada
            </p>

            <div className="ca-qty-row">
              <label className="ca-field">
                <span>Entradas a comprar</span>
                <div className="ca-qty">
                  <button type="button" onClick={() => changeQty(-1)} aria-label="Menos">
                    −
                  </button>
                  <input
                    type="number"
                    value={quantity}
                    min={1}
                    max={maxQty}
                    onChange={(e) => {
                      const v = Number(e.target.value) || 1;
                      setQuantity(Math.max(1, Math.min(maxQty, v)));
                    }}
                  />
                  <button type="button" onClick={() => changeQty(1)} aria-label="Más">
                    +
                  </button>
                </div>
              </label>

              <div className="ca-seat-legend">
                <span className="ca-legend">
                  <i className="ca-dot free" />
                  Libre
                </span>
                <span className="ca-legend">
                  <i className="ca-dot selected" />
                  Tu selección
                </span>
                <span className="ca-legend">
                  <i className="ca-dot reserved" />
                  Ocupada
                </span>
              </div>
            </div>

            <SeatMap seatMap={seatMap} selected={selected} onToggle={toggleSeat} />

            <Form.Group className="mb-3">
              <Form.Label>A nombre de</Form.Label>
              <Form.Control
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                required
                maxLength={150}
              />
            </Form.Group>

            <div className="ca-booking-summary">
              <div className="row">
                <span>Butacas seleccionadas</span>
                <b>{selectedList.length ? selectedList.join(", ") : "—"}</b>
              </div>
              <div className="row">
                <span>Precio unitario</span>
                <b>{price(unitPrice)}</b>
              </div>
              <div className="row total">
                <span>Total</span>
                <b>{price(unitPrice * quantity)}</b>
              </div>
            </div>

            <button type="submit" className="ca-btn ca-btn-primary ca-btn-block" disabled={!ready || submitting}>
              {submitting
                ? "Procesando…"
                : ready
                  ? `Confirmar ${quantity} entrada(s)`
                  : `Selecciona ${quantity} butaca(s) · ${selectedList.length}/${quantity}`}
            </button>
          </form>
        )}
      </Modal.Body>
    </Modal>
  );
}
