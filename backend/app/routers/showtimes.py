"""Endpoints del módulo de Sesiones/Funciones (Showtimes)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..auth import require_staff
from ..database import get_db
from ..models import Movie, ReservedSeat, Showtime, Ticket, User
from ..pagination import Page, PageParams, paginate
from ..schemas import (
    SeatMap,
    SeatRow,
    SeatStatus,
    ShowtimeCreate,
    ShowtimeRead,
    ShowtimeUpdate,
)
from ..seats import SEATS_PER_ROW, seat_layout

router = APIRouter(prefix="/showtimes", tags=["Funciones"])


@router.get("", response_model=Page[ShowtimeRead], summary="Listar funciones (paginado)")
def list_showtimes(
    movie_id: int | None = Query(default=None, description="Filtrar por película"),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """Devuelve las funciones disponibles de forma paginada.

    Admite el filtro opcional ``?movie_id=`` y la paginación ``?page=&size=``.
    """
    stmt = (
        select(Showtime)
        .options(selectinload(Showtime.movie))
        .order_by(Showtime.start_time)
    )
    if movie_id is not None:
        stmt = stmt.where(Showtime.movie_id == movie_id)
    return paginate(db, stmt, params)


@router.post(
    "",
    response_model=ShowtimeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una función (manager o admin)",
)
def create_showtime(
    payload: ShowtimeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> Showtime:
    """Crea una nueva función. **Requiere rol manager o admin.**

    Valida que la película exista y que los asientos disponibles no superen el
    aforo total. Si no se indica ``available_seats``, se inicializa al total.
    """
    movie = db.get(Movie, payload.movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="La película indicada no existe")

    available = payload.available_seats
    if available is None:
        available = payload.total_seats
    if available > payload.total_seats:
        raise HTTPException(
            status_code=400,
            detail="available_seats no puede ser mayor que total_seats",
        )

    showtime = Showtime(
        movie_id=payload.movie_id,
        room=payload.room,
        start_time=payload.start_time,
        total_seats=payload.total_seats,
        available_seats=available,
        price=payload.price,
    )
    db.add(showtime)
    db.commit()
    db.refresh(showtime)
    return showtime


@router.get(
    "/{showtime_id}/seats",
    response_model=SeatMap,
    summary="Mapa de asientos de una función",
)
def get_seat_map(showtime_id: int, db: Session = Depends(get_db)) -> SeatMap:
    """Devuelve el plano completo de butacas de una función.

    Cada butaca indica si está ``reserved`` (ocupada) o libre, de modo que el
    cliente pueda elegir sus asientos antes de comprar. La disposición coincide
    exactamente con la que valida el endpoint de compra.
    """
    showtime = db.get(Showtime, showtime_id)
    if showtime is None:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    reserved = set(
        db.scalars(
            select(ReservedSeat.seat_label).where(
                ReservedSeat.showtime_id == showtime_id
            )
        ).all()
    )

    rows = [
        SeatRow(
            row=label,
            seats=[SeatStatus(label=seat, reserved=seat in reserved) for seat in seats],
        )
        for label, seats in seat_layout(showtime.total_seats)
    ]

    return SeatMap(
        showtime_id=showtime.id,
        room=showtime.room,
        total_seats=showtime.total_seats,
        available_seats=showtime.available_seats,
        seats_per_row=SEATS_PER_ROW,
        reserved=sorted(reserved),
        rows=rows,
    )


@router.get("/{showtime_id}", response_model=ShowtimeRead, summary="Obtener una función por ID")
def get_showtime(showtime_id: int, db: Session = Depends(get_db)) -> Showtime:
    showtime = db.get(Showtime, showtime_id)
    if showtime is None:
        raise HTTPException(status_code=404, detail="Función no encontrada")
    return showtime


@router.put(
    "/{showtime_id}",
    response_model=ShowtimeRead,
    summary="Modificar una función (manager o admin)",
)
def update_showtime(
    showtime_id: int,
    payload: ShowtimeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> Showtime:
    """Actualiza los datos de una función. **Requiere rol manager o admin.**

    Reglas para no romper la sala:

    * La película debe existir.
    * El nuevo aforo no puede ser menor que las butacas ya vendidas.
    * ``available_seats`` no se acepta manualmente: se **recalcula** como
      ``aforo - butacas reservadas``.
    """
    showtime = db.get(Showtime, showtime_id)
    if showtime is None:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    if payload.movie_id is not None and db.get(Movie, payload.movie_id) is None:
        raise HTTPException(status_code=404, detail="La película indicada no existe")

    occupied = (
        db.scalar(
            select(func.count())
            .select_from(ReservedSeat)
            .where(ReservedSeat.showtime_id == showtime_id)
        )
        or 0
    )

    if payload.total_seats is not None and payload.total_seats < occupied:
        raise HTTPException(
            status_code=400,
            detail=(
                f"El aforo no puede ser menor que las butacas ya vendidas "
                f"({occupied})."
            ),
        )

    if payload.movie_id is not None:
        showtime.movie_id = payload.movie_id
    if payload.room is not None:
        showtime.room = payload.room
    if payload.start_time is not None:
        showtime.start_time = payload.start_time
    if payload.price is not None:
        showtime.price = payload.price
    if payload.total_seats is not None:
        showtime.total_seats = payload.total_seats

    # El aforo disponible siempre se desprende de las butacas realmente vendidas.
    showtime.available_seats = showtime.total_seats - occupied

    db.commit()
    db.refresh(showtime)
    return showtime


@router.delete(
    "/{showtime_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una función (manager o admin)",
)
def delete_showtime(
    showtime_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Elimina una función. **Requiere rol manager o admin.**

    No se permite eliminar una función con entradas vendidas (``409``) para no
    borrar reservas de clientes por accidente.
    """
    showtime = db.get(Showtime, showtime_id)
    if showtime is None:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    sold = (
        db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.showtime_id == showtime_id)
        )
        or 0
    )
    if sold:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: la función tiene entradas vendidas.",
        )

    db.delete(showtime)
    db.commit()

