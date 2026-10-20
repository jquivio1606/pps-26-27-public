"""Utilidades para el mapa de butacas de cada función.

El aforo de una función (``total_seats``) se distribuye en filas con un máximo
de :data:`SEATS_PER_ROW` asientos. Las filas se etiquetan ``A``, ``B``, ... (y,
si hiciera falta, ``AA``, ``AB``, ...) y cada butaca combina letra de fila y
número de columna, p. ej. ``A1``, ``A10``, ``B3``.

Estas funciones son la única fuente de verdad del "plano" de la sala, de modo
que backend y frontend coinciden exactamente en qué butacas existen.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

# Número de butacas por fila (ancho de la sala).
SEATS_PER_ROW = 10


def row_label(index: int) -> str:
    """Devuelve la etiqueta de fila para un índice 0-based (0->A, 25->Z, 26->AA)."""
    label = ""
    n = index + 1
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        label = chr(65 + remainder) + label
    return label


def seat_layout(total_seats: int) -> list[tuple[str, list[str]]]:
    """Reparte ``total_seats`` butacas en filas de :data:`SEATS_PER_ROW`.

    Devuelve una lista de tuplas ``(letra_fila, [etiquetas de butaca])``.
    """
    rows: list[tuple[str, list[str]]] = []
    remaining = total_seats
    index = 0
    while remaining > 0:
        count = min(SEATS_PER_ROW, remaining)
        label = row_label(index)
        rows.append((label, [f"{label}{col}" for col in range(1, count + 1)]))
        remaining -= count
        index += 1
    return rows


def all_seat_labels(total_seats: int) -> list[str]:
    """Lista plana con todas las butacas válidas de una función."""
    return [seat for _, seats in seat_layout(total_seats) for seat in seats]


def normalize_seat(label: str) -> str:
    """Normaliza una etiqueta de butaca (sin espacios y en mayúsculas)."""
    return label.strip().upper()


def is_valid_seat(total_seats: int, label: str) -> bool:
    """Indica si ``label`` corresponde a una butaca existente en la sala."""
    return normalize_seat(label) in set(all_seat_labels(total_seats))


def reconcile_reserved_seats(db: Session) -> None:
    """Alinea las butacas reservadas con el aforo disponible de cada función.

    Es una salvaguarda para bases de datos antiguas: si una función ya tenía
    entradas vendidas *antes* de existir la selección de butacas, su
    ``available_seats`` es menor que su aforo pero no hay butacas reservadas
    registradas. Aquí se marcan esas butacas "heredadas" para que el mapa de
    asientos sea coherente con el aforo.
    """
    from .models import ReservedSeat, Showtime  # import perezoso para evitar ciclos

    for showtime in db.scalars(select(Showtime)).all():
        reserved = set(
            db.scalars(
                select(ReservedSeat.seat_label).where(
                    ReservedSeat.showtime_id == showtime.id
                )
            ).all()
        )
        missing = (showtime.total_seats - showtime.available_seats) - len(reserved)
        if missing <= 0:
            continue
        free = [s for s in all_seat_labels(showtime.total_seats) if s not in reserved]
        for label in free[-missing:]:
            db.add(ReservedSeat(showtime_id=showtime.id, seat_label=label, ticket_id=None))
    db.commit()
