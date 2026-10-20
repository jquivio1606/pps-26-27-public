"""Esquemas Pydantic (validación de entrada y formato de salida)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# --------------------------------------------------------------------------- #
#  Autenticación / Usuarios
# --------------------------------------------------------------------------- #
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["ana"])
    email: EmailStr = Field(..., examples=["ana@example.com"])
    password: str = Field(..., min_length=6, max_length=72, examples=["secreto123"])


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime


class Token(BaseModel):
    """Respuesta del endpoint de login (formato OAuth2)."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    username: str | None = None
    role: str | None = None


class UserUpdate(BaseModel):
    """Cambios que el administrador puede aplicar a un usuario (parciales)."""

    role: str | None = Field(
        default=None,
        description="Nuevo rol: user, manager o admin.",
        examples=["manager"],
    )
    email: EmailStr | None = Field(default=None, examples=["jefe@cinema.com"])

    @field_validator("role")
    @classmethod
    def _rol_valido(cls, value: str | None) -> str | None:
        if value is not None and value not in ("user", "manager", "admin"):
            raise ValueError("Rol no válido. Usa: user, manager o admin")
        return value


class UserPasswordReset(BaseModel):
    """Nueva clave para un usuario, indicada por el administrador.

    Se guarda siempre hasheada con bcrypt: la clave en claro nunca se
    almacena ni se devuelve por la API.
    """

    password: str = Field(..., min_length=6, max_length=72, examples=["nuevaClave123"])


class Message(BaseModel):
    """Respuesta genérica con un mensaje de confirmación."""

    message: str


# --------------------------------------------------------------------------- #
#  Películas
# --------------------------------------------------------------------------- #
class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Origen"])
    genre: str = Field(..., min_length=1, max_length=100, examples=["Ciencia ficción"])
    duration_minutes: int = Field(..., gt=0, examples=[148])
    poster_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL de la imagen (póster). Opcional.",
        examples=["https://upload.wikimedia.org/wikipedia/en/d/db/The_Matrix.png"],
    )


class MovieCreate(MovieBase):
    """Datos necesarios para crear una película."""


class MovieRead(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# --------------------------------------------------------------------------- #
#  Sesiones / Funciones
# --------------------------------------------------------------------------- #
class ShowtimeBase(BaseModel):
    movie_id: int = Field(..., gt=0, examples=[1])
    room: str = Field(..., min_length=1, max_length=50, examples=["Sala 1"])
    start_time: datetime = Field(..., examples=["2026-10-13T18:00:00"])
    total_seats: int = Field(..., gt=0, examples=[100])
    price: float = Field(default=0.0, ge=0, examples=[9.5])


class ShowtimeCreate(ShowtimeBase):
    """Datos para crear una función.

    ``available_seats`` es opcional: si no se indica, se inicializa al total.
    """

    available_seats: int | None = Field(default=None, ge=0)


class ShowtimeRead(ShowtimeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    available_seats: int
    movie: MovieRead | None = None


class ShowtimeUpdate(BaseModel):
    """Cambios permitidos sobre una función (todos los campos son opcionales).

    No se admite cambiar ``available_seats`` directamente: el servidor lo
    recalcula a partir de las butacas ya reservadas, así que no se pueden
    "inventar" asientos ni romper el aforo por accidente.
    """

    movie_id: int | None = Field(default=None, gt=0, examples=[1])
    room: str | None = Field(default=None, min_length=1, max_length=50, examples=["Sala 2"])
    start_time: datetime | None = Field(default=None, examples=["2026-10-14T20:00:00"])
    total_seats: int | None = Field(default=None, gt=0, examples=[120])
    price: float | None = Field(default=None, ge=0, examples=[9.0])


# --------------------------------------------------------------------------- #
#  Mapa de asientos
# --------------------------------------------------------------------------- #
class SeatStatus(BaseModel):
    """Estado de una butaca concreta."""

    label: str = Field(..., examples=["A1"])
    reserved: bool = Field(..., description="True si ya está ocupada")


class SeatRow(BaseModel):
    """Una fila de butacas de la sala."""

    row: str = Field(..., examples=["A"])
    seats: list[SeatStatus]


class SeatMap(BaseModel):
    """Plano completo de asientos de una función."""

    showtime_id: int
    room: str
    total_seats: int
    available_seats: int
    seats_per_row: int
    reserved: list[str]
    rows: list[SeatRow]


# --------------------------------------------------------------------------- #
#  Reservas / Entradas
# --------------------------------------------------------------------------- #
class TicketBookRequest(BaseModel):
    """Datos para comprar entradas.

    Se puede indicar la cantidad de entradas (``quantity``) y/o la lista de
    butacas elegidas (``seats``). Reglas:

    * El número de butacas debe coincidir con la cantidad de entradas.
    * No se puede repetir la misma butaca dentro de una compra.
    * Si se omiten las butacas, se asignan automáticamente las primeras libres.
    """

    showtime_id: int = Field(..., gt=0, examples=[1])
    customer_name: str = Field(..., min_length=1, max_length=150, examples=["Ana López"])
    quantity: int | None = Field(default=None, gt=0, examples=[2])
    seats: list[str] | None = Field(default=None, max_length=50, examples=[["A1", "A2"]])

    @model_validator(mode="after")
    def _exige_cantidad_o_asientos(self) -> "TicketBookRequest":
        if self.quantity is None and not self.seats:
            raise ValueError("Debes indicar 'quantity' o una lista de 'seats'")
        return self


class TicketRead(BaseModel):
    """Una reserva con sus butacas y los datos para identificarla.

    Además de los datos propios de la compra se incluye el **usuario comprador**
    (``username``) y un resumen de la función (``movie_title``, ``room`` y
    ``start_time``). Todos esos campos son opcionales porque dependen de que la
    reserva llegue con sus relaciones accesibles; sirven para que el personal
    (manager o admin) reconozca de un vistazo de quién es cada entrada.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    showtime_id: int
    user_id: int | None = None
    customer_name: str
    quantity: int
    total_price: float
    seats: list[str] = Field(default_factory=list)
    created_at: datetime
    username: str | None = Field(
        default=None, description="Usuario que realizó la compra (si está vinculada)"
    )
    movie_title: str | None = Field(default=None, description="Película de la función")
    room: str | None = Field(default=None, description="Sala de la función")
    start_time: datetime | None = Field(
        default=None, description="Fecha y hora de la función"
    )

    @field_validator("seats", mode="before")
    @classmethod
    def _etiquetas_de_butaca(cls, value: object) -> list[str]:
        """Convierte la relación de butacas ORM en una lista de etiquetas."""
        if value is None:
            return []
        return [getattr(seat, "seat_label", seat) for seat in value]  # type: ignore[arg-type]

    @model_validator(mode="before")
    @classmethod
    def _desde_objeto_orm(cls, value: object) -> object:
        """Rellena los campos de usuario y función desde las relaciones ORM."""
        if isinstance(value, dict) or value is None:
            return value
        user = getattr(value, "user", None)
        showtime = getattr(value, "showtime", None)
        movie = getattr(showtime, "movie", None)
        return {
            "id": getattr(value, "id", None),
            "showtime_id": getattr(value, "showtime_id", None),
            "user_id": getattr(value, "user_id", None),
            "customer_name": getattr(value, "customer_name", None),
            "quantity": getattr(value, "quantity", None),
            "total_price": getattr(value, "total_price", None),
            "seats": getattr(value, "seats", None),
            "created_at": getattr(value, "created_at", None),
            "username": getattr(user, "username", None),
            "movie_title": getattr(movie, "title", None),
            "room": getattr(showtime, "room", None),
            "start_time": getattr(showtime, "start_time", None),
        }


class TicketBookResponse(BaseModel):
    """Respuesta de una compra confirmada."""

    message: str = "Compra realizada con éxito"
    ticket: TicketRead
    showtime_id: int
    remaining_seats: int


# --------------------------------------------------------------------------- #
#  Estadísticas / panel del personal
# --------------------------------------------------------------------------- #
class MovieStat(BaseModel):
    """Rendimiento de una película en el panel de estadísticas."""

    movie_id: int
    title: str
    showtimes: int
    tickets: int
    seats_sold: int
    revenue: float


class DashboardStats(BaseModel):
    """Resumen agregado de la actividad de la web (manager y admin)."""

    movies: int
    showtimes: int
    users: int
    users_by_role: dict[str, int]
    tickets: int = Field(..., description="Número de reservas")
    seats_sold: int = Field(..., description="Entradas vendidas")
    revenue: float = Field(..., description="Ingresos totales")
    seats_total: int
    seats_reserved: int
    seats_available: int
    occupancy_percent: float = Field(..., description="Ocupación media de las salas (%)")
    top_movies: list[MovieStat]
    recent_tickets: list[TicketRead]


class TechItem(BaseModel):
    """Una tecnología usada por el sistema (solo admin / informático)."""

    name: str = Field(..., examples=["FastAPI"])
    version: str = Field(default="", examples=["0.115.6"])
    group: str = Field(
        default="Servidor",
        description="Bloque al que pertenece: Servidor, Datos o Seguridad.",
    )
    purpose: str = Field(default="", description="Para qué se usa en este proyecto.")


class SystemInfo(BaseModel):
    """Información técnica del sistema (solo admin / informático).

    Nunca incluye secretos: se indica si la ``SECRET_KEY`` está configurada,
    pero no su valor.
    """

    app: str
    version: str
    database: str = Field(..., description="Motor de base de datos (sin credenciales)")
    secret_key_configured: bool = Field(..., description="False si se usa la clave por defecto")
    access_token_expire_minutes: int = Field(
        ..., description="Minutos de validez del token antes de pedir login de nuevo"
    )
    token_algorithm: str = Field(..., description="Algoritmo de firma del JWT")
    password_hashing: str
    users_total: int
    users_hashed: int = Field(..., description="Usuarios con la clave cifrada (bcrypt)")
    tables: dict[str, int]
    technologies: list[TechItem] = Field(
        default_factory=list,
        description="Tecnologías del backend con su versión y uso.",
    )
    docs: str
    redoc: str
    openapi: str
