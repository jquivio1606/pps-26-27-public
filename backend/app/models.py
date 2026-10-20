"""Modelos ORM (tablas de la base de datos)."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """Usuario de la API (clientes y administradores)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Rol: "user" (cliente), "manager" (jefe: catálogo + estadísticas)
    # o "admin" (informático: gestión de usuarios y del sistema).
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="user")


class Movie(Base):
    """Película en cartelera."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # URL de la imagen (póster). Opcional: si falta, el frontend dibuja un diseño propio.
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    showtimes: Mapped[list["Showtime"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_movies_duration_positive"),
    )


class Showtime(Base):
    """Función / sesión de una película en una sala y hora concretas."""

    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    # Precio por entrada (opcional, por defecto 0). Facilita el cálculo del total.
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    movie: Mapped["Movie"] = relationship(back_populates="showtimes")
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="showtime", cascade="all, delete-orphan"
    )
    reserved_seats: Mapped[list["ReservedSeat"]] = relationship(
        back_populates="showtime", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_seats > 0", name="ck_showtimes_total_seats_positive"),
        CheckConstraint(
            "available_seats >= 0 AND available_seats <= total_seats",
            name="ck_showtimes_available_seats_range",
        ),
    )


class Ticket(Base):
    """Reserva / compra de entradas realizada por un cliente."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtimes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Usuario autenticado que realizó la compra (nullable por compatibilidad).
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    showtime: Mapped["Showtime"] = relationship(back_populates="tickets")
    user: Mapped["User | None"] = relationship(back_populates="tickets")
    seats: Mapped[list["ReservedSeat"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_tickets_quantity_positive"),
    )


class ReservedSeat(Base):
    """Butaca concreta reservada dentro de una función.

    La restricción única ``(showtime_id, seat_label)`` garantiza a nivel de base
    de datos que **dos entradas no puedan ocupar la misma butaca**.
    """

    __tablename__ = "reserved_seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtimes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seat_label: Mapped[str] = mapped_column(String(10), nullable=False)
    # Entrada que ocupa la butaca. Nullable para butacas "heredadas" (compras
    # anteriores a la selección de asientos) o si la entrada se elimina.
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True
    )

    showtime: Mapped["Showtime"] = relationship(back_populates="reserved_seats")
    ticket: Mapped["Ticket | None"] = relationship(back_populates="seats")

    __table_args__ = (
        UniqueConstraint("showtime_id", "seat_label", name="uq_showtime_seat"),
    )
