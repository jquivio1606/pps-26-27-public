/**
 * Plano de butacas. `selected` es un Set de etiquetas y `onToggle(label)`
 * avisa de la selección. Las butacas reservadas quedan deshabilitadas.
 */
export default function SeatMap({ seatMap, selected, onToggle }) {
  return (
    <>
      <div className="ca-screen">PANTALLA</div>

      <div className="ca-seat-map">
        {seatMap.rows.map((row) => (
          <div className="ca-seat-row" key={row.row}>
            <span className="ca-seat-row-label">{row.row}</span>
            <div className="ca-seat-row-seats">
              {row.seats.map((seat) => {
                const isSelected = selected.has(seat.label);
                return (
                  <button
                    type="button"
                    key={seat.label}
                    className={`ca-seat${seat.reserved ? " reserved" : ""}${isSelected ? " selected" : ""}`}
                    disabled={seat.reserved}
                    aria-pressed={isSelected}
                    aria-label={`Butaca ${seat.label}${seat.reserved ? " ocupada" : ""}`}
                    title={`${seat.label}${seat.reserved ? " (ocupada)" : ""}`}
                    onClick={() => onToggle(seat.label, seat.reserved)}
                  >
                    {seat.label.slice(1)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
