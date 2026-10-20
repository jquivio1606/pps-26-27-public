"""Endpoints del módulo de Estadísticas y del sistema.

* ``GET /stats/dashboard`` -> resumen de actividad de la web (manager o admin).
* ``GET /stats/system``    -> información técnica (solo admin / informático).
"""

import platform
import sqlite3
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from .. import __version__
from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    DEFAULT_SECRET_KEY,
    ROLES,
    SECRET_KEY,
    is_hashed_password,
    require_admin,
    require_staff,
)
from ..database import DATABASE_URL, get_db
from ..models import Movie, ReservedSeat, Showtime, Ticket, User
from ..schemas import DashboardStats, MovieStat, SystemInfo, TechItem

router = APIRouter(prefix="/stats", tags=["Estadísticas"])

TOP_MOVIES = 5
RECENT_TICKETS = 5


def _count(db: Session, model) -> int:
    """Cuenta las filas de un modelo (devuelve 0 si la tabla está vacía)."""
    return db.scalar(select(func.count()).select_from(model)) or 0


def _safe_database_url(url: str) -> str:
    """Devuelve la URL de la base de datos sin credenciales (usuario:clave@)."""
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if "@" in rest:
        rest = rest.split("@", 1)[1]
    return f"{scheme}://{rest}"


def _installed(package: str) -> str:
    """Versión instalada de un paquete («desconocida» si no está declarada)."""
    try:
        return pkg_version(package)
    except PackageNotFoundError:
        return "desconocida"


def _technologies() -> list[TechItem]:
    """Tecnologías del backend con su versión real instalada y su propósito.

    Es información técnica para el perfil admin: no expone secretos, solo la
    pila sobre la que corre el servicio.
    """
    if DATABASE_URL.startswith("sqlite"):
        db_name = f"SQLite {sqlite3.sqlite_version}"
    else:
        db_name = DATABASE_URL.split("://", 1)[0]
    return [
        TechItem(
            name="Python",
            version=platform.python_version(),
            group="Servidor",
            purpose="Lenguaje del backend",
        ),
        TechItem(
            name="FastAPI",
            version=_installed("fastapi"),
            group="Servidor",
            purpose="Framework web y API REST",
        ),
        TechItem(
            name="Uvicorn",
            version=_installed("uvicorn"),
            group="Servidor",
            purpose="Servidor ASGI que ejecuta la app",
        ),
        TechItem(
            name="SQLAlchemy",
            version=_installed("sqlalchemy"),
            group="Datos",
            purpose="ORM y acceso a la base de datos",
        ),
        TechItem(
            name=db_name,
            version="",
            group="Datos",
            purpose="Base de datos (sin credenciales)",
        ),
        TechItem(
            name="Pydantic",
            version=_installed("pydantic"),
            group="Datos",
            purpose="Validación y serialización de datos",
        ),
        TechItem(
            name="PyJWT",
            version=_installed("PyJWT"),
            group="Seguridad",
            purpose=f"Firma y verificación de tokens ({ALGORITHM})",
        ),
        TechItem(
            name="bcrypt",
            version=_installed("bcrypt"),
            group="Seguridad",
            purpose="Cifrado de contraseñas",
        ),
    ]


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Estadísticas de la web (manager o admin)",
)
def dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> DashboardStats:
    """Resumen agregado de la actividad de la web.

    **Requiere rol manager o admin.** Incluye ventas, ocupación de las salas,
    reparto de usuarios por rol, películas más taquilleras y las últimas
    reservas. Todos los datos son agregados: el manager obtiene la foto global
    de la web sin necesidad de acceso a la gestión de usuarios.
    """
    movies = _count(db, Movie)
    showtimes = _count(db, Showtime)
    users = _count(db, User)
    tickets = _count(db, Ticket)

    seats_sold = int(db.scalar(select(func.coalesce(func.sum(Ticket.quantity), 0))) or 0)
    revenue = float(
        db.scalar(select(func.coalesce(func.sum(Ticket.total_price), 0.0))) or 0.0
    )

    seats_total = int(
        db.scalar(select(func.coalesce(func.sum(Showtime.total_seats), 0))) or 0
    )
    seats_available = int(
        db.scalar(select(func.coalesce(func.sum(Showtime.available_seats), 0))) or 0
    )
    seats_reserved = max(seats_total - seats_available, 0)
    occupancy = round(seats_reserved / seats_total * 100, 1) if seats_total else 0.0

    users_by_role = {
        role: int(
            db.scalar(
                select(func.count()).select_from(User).where(User.role == role)
            )
            or 0
        )
        for role in ROLES
    }

    # Películas más taquilleras (por ingresos; las que no venden también salen).
    top_stmt = (
        select(
            Movie.id,
            Movie.title,
            func.count(func.distinct(Showtime.id)),
            func.count(func.distinct(Ticket.id)),
            func.coalesce(func.sum(Ticket.quantity), 0),
            func.coalesce(func.sum(Ticket.total_price), 0.0),
        )
        .select_from(Movie)
        .outerjoin(Showtime, Showtime.movie_id == Movie.id)
        .outerjoin(Ticket, Ticket.showtime_id == Showtime.id)
        .group_by(Movie.id)
        .order_by(
            func.coalesce(func.sum(Ticket.total_price), 0.0).desc(), Movie.title
        )
        .limit(TOP_MOVIES)
    )
    top_movies = [
        MovieStat(
            movie_id=row[0],
            title=row[1],
            showtimes=int(row[2]),
            tickets=int(row[3]),
            seats_sold=int(row[4]),
            revenue=round(float(row[5]), 2),
        )
        for row in db.execute(top_stmt).all()
    ]

    recent = list(
        db.scalars(
            select(Ticket)
            .options(selectinload(Ticket.seats))
            .order_by(Ticket.id.desc())
            .limit(RECENT_TICKETS)
        ).all()
    )

    return DashboardStats(
        movies=movies,
        showtimes=showtimes,
        users=users,
        users_by_role=users_by_role,
        tickets=tickets,
        seats_sold=seats_sold,
        revenue=round(revenue, 2),
        seats_total=seats_total,
        seats_reserved=seats_reserved,
        seats_available=seats_available,
        occupancy_percent=occupancy,
        top_movies=top_movies,
        recent_tickets=recent,
    )


@router.get(
    "/system",
    response_model=SystemInfo,
    summary="Información técnica del sistema (solo admin)",
)
def system_info(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SystemInfo:
    """Datos de operación para el perfil informático. **Requiere rol admin.**

    Muestra el estado del sistema *sin exponer secretos*: indica si la
    ``SECRET_KEY`` está configurada (nunca su valor) y cuántos usuarios tienen
    la clave cifrada con bcrypt.
    """
    users = list(db.scalars(select(User)).all())
    users_hashed = sum(1 for user in users if is_hashed_password(user.hashed_password))

    return SystemInfo(
        app="Cinema API",
        version=__version__,
        database=_safe_database_url(DATABASE_URL),
        secret_key_configured=SECRET_KEY != DEFAULT_SECRET_KEY,
        access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        token_algorithm=ALGORITHM,
        password_hashing="bcrypt",
        users_total=len(users),
        users_hashed=users_hashed,
        tables={
            "users": len(users),
            "movies": _count(db, Movie),
            "showtimes": _count(db, Showtime),
            "tickets": _count(db, Ticket),
            "reserved_seats": _count(db, ReservedSeat),
        },
        technologies=_technologies(),
        docs="/docs",
        redoc="/redoc",
        openapi="/openapi.json",
    )
