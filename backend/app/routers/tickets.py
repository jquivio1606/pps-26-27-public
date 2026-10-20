"""Endpoints del módulo de Reservas/Entradas (Tickets)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..auth import get_current_user, is_admin, is_staff, require_staff
from ..database import get_db
from ..models import ReservedSeat, Showtime, Ticket, User
from ..pagination import Page, PageParams, paginate
from ..schemas import TicketBookRequest, TicketBookResponse, TicketRead
from ..seats import all_seat_labels, is_valid_seat, normalize_seat

router = APIRouter(prefix="/tickets", tags=["Reservas"])


@router.post(
    "/book",
    response_model=TicketBookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Comprar / reservar entradas (requiere autenticación)",
    responses={
        400: {"description": "Datos inválidos: sin asientos suficientes o butacas mal indicadas"},
        401: {"description": "No autenticado"},
        404: {"description": "La función indicada no existe"},
        409: {"description": "Alguna de las butacas elegidas ya está ocupada"},
    },
)
def book_ticket(
    payload: TicketBookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketBookResponse:
    """Reserva entradas para una función concreta. **Requiere estar autenticado.**

    **Selección de asientos.** Se puede enviar la lista de butacas elegidas en
    ``seats`` (p. ej. ``["A1", "A2"]``). Reglas aplicadas:

    * El número de butacas debe coincidir con la cantidad de entradas.
    * No se puede repetir la misma butaca dentro de una compra.
    * Una butaca ya reservada no puede asignarse a otra entrada (``409``).

    Si se omite ``seats``, se asignan automáticamente las primeras butacas libres
    (útil para clientes que no necesitan elegir). Antes de confirmar se comprueba
    que queden asientos suficientes; si no, se devuelve ``400``.
    """
    # Bloqueo pesimista de la fila (en SQLite es inocuo; en PostgreSQL/MySQL evita
    # condiciones de carrera cuando hay compras concurrentes).
    showtime = db.execute(
        select(Showtime).where(Showtime.id == payload.showtime_id).with_for_update()
    ).scalar_one_or_none()

    if showtime is None:
        raise HTTPException(status_code=404, detail="La función indicada no existe")

    # Butacas ya ocupadas en esta función.
    taken = set(
        db.scalars(
            select(ReservedSeat.seat_label).where(
                ReservedSeat.showtime_id == showtime.id
            )
        ).all()
    )

    requested: list[str]

    if payload.seats:
        requested = [normalize_seat(seat) for seat in payload.seats]

        # No se puede repetir la misma butaca en una misma compra.
        if len(set(requested)) != len(requested):
            raise HTTPException(
                status_code=400,
                detail="No puedes seleccionar la misma butaca más de una vez.",
            )

        # El número de butacas debe coincidir con el número de entradas.
        if payload.quantity is not None and payload.quantity != len(requested):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Has elegido {len(requested)} butaca(s) pero indicaste "
                    f"{payload.quantity} entrada(s). Deben coincidir."
                ),
            )

        invalid = [seat for seat in requested if not is_valid_seat(showtime.total_seats, seat)]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Estas butacas no existen en la sala: "
                    f"{', '.join(sorted(set(invalid)))}."
                ),
            )

        occupied = [seat for seat in requested if seat in taken]
        if occupied:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Estas butacas ya están ocupadas: "
                    f"{', '.join(sorted(occupied))}. Elige otras."
                ),
            )
    else:
        # Sin butacas indicadas: se asignan automáticamente las primeras libres.
        quantity = payload.quantity  # garantizado no nulo por el esquema
        assert quantity is not None
        free = [seat for seat in all_seat_labels(showtime.total_seats) if seat not in taken]
        if len(free) < quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No hay asientos suficientes. Solicitados: {quantity}, "
                    f"disponibles: {len(free)}."
                ),
            )
        requested = free[:quantity]

    quantity = len(requested)

    if showtime.available_seats < quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No hay asientos suficientes. Solicitados: {quantity}, "
                f"disponibles: {showtime.available_seats}."
            ),
        )

    # Descontar asientos y registrar la reserva + sus butacas en la transacción.
    showtime.available_seats -= quantity
    ticket = Ticket(
        showtime_id=showtime.id,
        user_id=current_user.id,
        customer_name=payload.customer_name,
        quantity=quantity,
        total_price=round(quantity * showtime.price, 2),
    )
    db.add(ticket)
    db.flush()  # Para disponer de ticket.id antes de crear las butacas.

    for seat in requested:
        db.add(ReservedSeat(showtime_id=showtime.id, seat_label=seat, ticket_id=ticket.id))

    try:
        db.commit()
    except IntegrityError:
        # Otra compra concurrente reservó una de las butacas justo antes.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alguna de las butacas acaba de ser ocupada. Inténtalo de nuevo.",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al procesar la reserva")

    db.refresh(ticket)
    db.refresh(showtime)
    return TicketBookResponse(
        ticket=TicketRead.model_validate(ticket),
        showtime_id=showtime.id,
        remaining_seats=showtime.available_seats,
    )


@router.get(
    "",
    response_model=Page[TicketRead],
    summary="Listar reservas (paginado)",
)
def list_tickets(
    showtime_id: int | None = Query(default=None, description="Filtrar por función"),
    scope: str | None = Query(
        default=None,
        pattern="^(mine|all)$",
        description=(
            "Alcance de la lista: 'all' devuelve **todas** las reservas "
            "(solo manager o admin) y 'mine' solo las del usuario actual. "
            "Si se omite: el admin ve todas y el resto las suyas."
        ),
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Filtra por nombre del cliente o por nombre de usuario",
    ),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Lista las reservas de forma paginada.

    * **Admin**: ve todas las reservas (también con ``?scope=all``).
    * **Manager**: ve las suyas por defecto y **todas** con ``?scope=all``
      (necesario para localizar y cancelar entradas de los clientes).
    * **Usuario normal**: ve únicamente las suyas; ``?scope=all`` -> ``403``.

    El parámetro ``?search=`` filtra por nombre del cliente o por usuario, lo
    que permite encontrar «las entradas de un jugador» concretamente.
    """
    if scope == "all" and not is_staff(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el personal (manager o admin) puede ver todas las reservas",
        )

    stmt = (
        select(Ticket)
        .options(
            selectinload(Ticket.seats),
            selectinload(Ticket.user),
            selectinload(Ticket.showtime).selectinload(Showtime.movie),
        )
        .order_by(Ticket.id)
    )

    # Alcance por defecto: admin -> todas; manager y usuario -> solo las suyas.
    if scope == "mine" or (scope is None and not is_admin(current_user)):
        stmt = stmt.where(Ticket.user_id == current_user.id)

    if showtime_id is not None:
        stmt = stmt.where(Ticket.showtime_id == showtime_id)

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Ticket.customer_name.ilike(pattern),
                Ticket.user.has(User.username.ilike(pattern)),
            )
        )

    return paginate(db, stmt, params)


@router.get("/{ticket_id}", response_model=TicketRead, summary="Obtener una reserva por ID")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Ticket:
    ticket = db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(
            selectinload(Ticket.seats),
            selectinload(Ticket.user),
            selectinload(Ticket.showtime).selectinload(Showtime.movie),
        )
    ).scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if not is_staff(current_user) and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta reserva",
        )
    return ticket


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar una reserva (manager o admin)",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Rol insuficiente (solo manager o admin)"},
        404: {"description": "La reserva indicada no existe"},
    },
)
def cancel_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Cancela una reserva y **libera sus butacas**. **Requiere rol manager o admin.**

    Pensado para el caso típico de que un cliente se haya equivocado al
    comprar: el personal cancela la entrada y las butacas vuelven a estar
    disponibles para una nueva compra (el aforo se recalcula con las butacas
    que quedan realmente reservadas, igual que en la edición de funciones).

    * No se guarda historial de la cancelación: la desaparece del listado.
    * **El reembolso del dinero no está implementado en la web** (tampoco lo
      está el pago: no hay pasarela de pago); el dinero se devuelve fuera de
      la plataforma.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    # Bloqueo de la función mientras se libera el aforo (en SQLite es inocuo).
    showtime = db.execute(
        select(Showtime).where(Showtime.id == ticket.showtime_id).with_for_update()
    ).scalar_one_or_none()

    # El borrado en cascada elimina las butacas vinculadas a la entrada
    # (relación Ticket.seats + FK ondelete=CASCADE en reserved_seats).
    db.delete(ticket)
    db.flush()

    if showtime is not None:
        occupied = (
            db.scalar(
                select(func.count())
                .select_from(ReservedSeat)
                .where(ReservedSeat.showtime_id == showtime.id)
            )
            or 0
        )
        # Mismo invariante que la edición de funciones: el aforo libre es el
        # total menos las butacas que siguen ocupadas en el mapa.
        showtime.available_seats = max(showtime.total_seats - occupied, 0)

    db.commit()
