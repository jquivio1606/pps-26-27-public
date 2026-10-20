"""Datos de prueba iniciales: usuarios, 20 películas y 10 funciones.

Se cargan automáticamente al arrancar la aplicación (solo lo que falte, sin
duplicar ni borrar datos). También se pueden cargar manualmente con:

    python -m app.seed
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import ensure_passwords_encrypted, hash_password
from .database import Base, SessionLocal, engine, run_light_migrations
from .models import Movie, Showtime, User
from .seats import reconcile_reserved_seats

# --------------------------------------------------------------------------- #
#  Usuarios de prueba
# --------------------------------------------------------------------------- #
USERS: list[dict] = [
    {"username": "admin", "email": "admin@cinema.com", "password": "admin123", "role": "admin"},
    {"username": "manager", "email": "manager@cinema.com", "password": "manager123", "role": "manager"},
    {"username": "user", "email": "user@cinema.com", "password": "user123", "role": "user"},
]


# --------------------------------------------------------------------------- #
#  20 películas (con póster real de Wikipedia; el frontend usa un respaldo
#  gráfico si la imagen no está disponible).
# --------------------------------------------------------------------------- #
MOVIES: list[dict] = [
    {"title": "El Padrino", "genre": "Drama", "duration_minutes": 175,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg"},
    {"title": "Pulp Fiction", "genre": "Crimen", "duration_minutes": 154,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg"},
    {"title": "El Caballero Oscuro", "genre": "Acción", "duration_minutes": 152,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/1/1c/The_Dark_Knight_%282008_film%29.jpg"},
    {"title": "Origen", "genre": "Ciencia ficción", "duration_minutes": 148,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg"},
    {"title": "Interstellar", "genre": "Ciencia ficción", "duration_minutes": 169,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg"},
    {"title": "Forrest Gump", "genre": "Drama", "duration_minutes": 142,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg"},
    {"title": "Matrix", "genre": "Ciencia ficción", "duration_minutes": 136,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/d/db/The_Matrix.png"},
    {"title": "Gladiator", "genre": "Acción", "duration_minutes": 155,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/f/fb/Gladiator_%282000_film_poster%29.png"},
    {"title": "Titanic", "genre": "Romance", "duration_minutes": 195,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/1/18/Titanic_%281997_film%29_poster.png"},
    {"title": "Parásitos", "genre": "Drama", "duration_minutes": 132,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/5/53/Parasite_%282019_film%29.png"},
    {"title": "El Señor de los Anillos", "genre": "Aventura", "duration_minutes": 178,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/f/fb/Lord_Rings_Fellowship_Ring.jpg"},
    {"title": "Star Wars: Una nueva esperanza", "genre": "Ciencia ficción", "duration_minutes": 121,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/8/87/StarWarsMoviePoster1977.jpg"},
    {"title": "Jurassic Park", "genre": "Aventura", "duration_minutes": 127,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/e/e7/Jurassic_Park_poster.jpg"},
    {"title": "El Club de la Lucha", "genre": "Drama", "duration_minutes": 139,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/f/fc/Fight_Club_poster.jpg"},
    {"title": "Coco", "genre": "Animación", "duration_minutes": 105,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/9/98/Coco_%282017_film%29_poster.jpg"},
    {"title": "Toy Story", "genre": "Animación", "duration_minutes": 81,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg"},
    {"title": "Whiplash", "genre": "Drama", "duration_minutes": 106,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/0/01/Whiplash_poster.jpg"},
    {"title": "La La Land", "genre": "Musical", "duration_minutes": 128,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/a/ab/La_La_Land_%28film%29.png"},
    {"title": "Mad Max: Furia en la carretera", "genre": "Acción", "duration_minutes": 120,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/6/6e/Mad_Max_Fury_Road.jpg"},
    {"title": "El Viaje de Chihiro", "genre": "Animación", "duration_minutes": 125,
     "poster_url": "https://upload.wikimedia.org/wikipedia/en/d/db/Spirited_Away_Japanese_poster.png"},
]

POSTERS_BY_TITLE: dict[str, str] = {m["title"]: m["poster_url"] for m in MOVIES}

# --------------------------------------------------------------------------- #
#  10 funciones (referencian películas por título)
# --------------------------------------------------------------------------- #
BASE_DAY = datetime(2026, 10, 13)

SHOWTIMES: list[dict] = [
    {"movie_title": "El Padrino", "room": "Sala 1", "start": BASE_DAY.replace(hour=16), "total_seats": 120, "price": 8.5},
    {"movie_title": "Pulp Fiction", "room": "Sala 2", "start": BASE_DAY.replace(hour=17, minute=30), "total_seats": 100, "price": 8.0},
    {"movie_title": "El Caballero Oscuro", "room": "Sala 3", "start": BASE_DAY.replace(hour=18), "total_seats": 150, "price": 9.5},
    {"movie_title": "Origen", "room": "Sala 4", "start": BASE_DAY.replace(hour=19), "total_seats": 90, "price": 9.0},
    {"movie_title": "Interstellar", "room": "Sala IMAX", "start": BASE_DAY.replace(hour=20), "total_seats": 200, "price": 12.0},
    {"movie_title": "Coco", "room": "Sala 5", "start": BASE_DAY.replace(hour=15), "total_seats": 80, "price": 7.0},
    {"movie_title": "Matrix", "room": "Sala 2", "start": BASE_DAY.replace(hour=21), "total_seats": 100, "price": 8.0},
    {"movie_title": "El Viaje de Chihiro", "room": "Sala 5", "start": BASE_DAY.replace(hour=18, minute=45), "total_seats": 80, "price": 7.5},
    {"movie_title": "Gladiator", "room": "Sala 3", "start": BASE_DAY + timedelta(days=1), "total_seats": 150, "price": 9.5},
    {"movie_title": "Whiplash", "room": "Sala 1", "start": BASE_DAY + timedelta(days=1, hours=2), "total_seats": 120, "price": 8.5},
]


def seed_users(db: Session) -> None:
    """Crea los usuarios de prueba que falten (uno a uno, por nombre).

    Es idempotente y también sirve para bases de datos ya existentes: si falta
    el usuario de pruebas ``manager`` (o ``admin``/``user``) se crea, sin tocar
    las cuentas que ya tengan ese nombre. Las claves se guardan hasheadas.
    """
    existing = set(db.scalars(select(User.username)).all())
    missing = [data for data in USERS if data["username"] not in existing]
    if not missing:
        return
    db.add_all(
        User(
            username=data["username"],
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            role=data["role"],
        )
        for data in missing
    )
    db.commit()


def seed_catalog(db: Session) -> None:
    """Inserta películas y funciones si la tabla de películas está vacía."""
    already_seeded = db.execute(select(Movie.id).limit(1)).first() is not None
    if already_seeded:
        return

    movies = [Movie(**data) for data in MOVIES]
    db.add_all(movies)
    db.flush()  # Asigna IDs a las películas antes de crear las funciones.

    movies_by_title = {movie.title: movie for movie in movies}

    showtimes = []
    for data in SHOWTIMES:
        movie = movies_by_title[data["movie_title"]]
        showtimes.append(
            Showtime(
                movie_id=movie.id,
                room=data["room"],
                start_time=data["start"],
                total_seats=data["total_seats"],
                available_seats=data["total_seats"],
                price=data["price"],
            )
        )
    db.add_all(showtimes)
    db.commit()


def seed_db(db: Session) -> None:
    """Carga usuarios y catálogo de prueba si aún no existen."""
    seed_users(db)
    seed_catalog(db)
    backfill_posters(db)


def backfill_posters(db: Session) -> None:
    """Rellena el póster de películas ya existentes que aún no lo tengan.

    Permite que una base de datos creada antes de esta función reciba los
    pósters sin perder datos. Para películas personalizadas (título no incluido
    en el catálogo de prueba) se deja ``None`` y el frontend dibuja su respaldo.
    """
    movies = db.scalars(select(Movie).where(Movie.poster_url.is_(None))).all()
    changed = False
    for movie in movies:
        url = POSTERS_BY_TITLE.get(movie.title)
        if url:
            movie.poster_url = url
            changed = True
    if changed:
        db.commit()


def init_db() -> None:
    """Crea las tablas y carga los datos de prueba (usado al arrancar)."""
    Base.metadata.create_all(bind=engine)
    run_light_migrations(engine)
    with SessionLocal() as db:
        seed_db(db)
        ensure_passwords_encrypted(db)
        reconcile_reserved_seats(db)


if __name__ == "__main__":
    init_db()
    print(
        "Base de datos inicializada con 3 usuarios, 20 películas y 10 funciones."
    )
