"""Configuración de la base de datos (SQLAlchemy 2.0).

Por defecto se usa SQLite (``backend/cinema.db``) para que la API sea
ejecutable de inmediato sin dependencias externas. En producción basta con
definir la variable de entorno ``DATABASE_URL`` con la cadena de conexión de
PostgreSQL (por ejemplo, la que ofrece Render).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Cargar variables de entorno desde .env si existe
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(_ENV_PATH)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# La base de datos vive junto al código, en ``backend/cinema.db``. Se usa una
# ruta absoluta para que no dependa del directorio desde el que se arranque.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SQLITE = (_BACKEND_DIR / "cinema.db").as_posix()

# Por defecto: ``backend/cinema.db``. Se puede sobrescribir con DATABASE_URL.
def normalize_database_url(url: str) -> str:
    """Adapta la URL para que SQLAlchemy use el driver correcto.

    Render (y Heroku) entregan la cadena como ``postgres://`` o
    ``postgresql://``, pero SQLAlchemy 2.x exige un driver explícito, así que
    se reescribe a ``postgresql+psycopg://``. Además, la URL *externa* de
    Render (la que termina en ``.render.com``) exige SSL, por lo que se añade
    ``sslmode=require`` si no viene indicado. La URL *interna* (red privada)
    se deja tal cual.
    """
    if not url or url.startswith("sqlite"):
        return url

    for prefix in ("postgres://", "postgresql://", "postgresql+psycopg2://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg://" + url.split("://", 1)[1]
            break

    parsed = make_url(url)
    host = (parsed.host or "").lower()
    if host.endswith(".render.com") and "sslmode" not in parsed.query:
        parsed = parsed.update_query_dict({"sslmode": "require"})
        url = parsed.render_as_string(hide_password=False)
    return url


DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE}")
)

#: ¿Se está usando SQLite? Algunas migraciones son específicas de ese motor.
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# ``check_same_thread`` solo es necesario para SQLite. En PostgreSQL se usa
# ``pool_pre_ping`` (descarta conexiones muertas) y ``pool_recycle`` (evita
# superar el tiempo máximo de conexión que impone el proveedor).
engine_kwargs: dict = {"future": True, "pool_pre_ping": True}
if IS_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI que entrega una sesión por petición y la cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_light_migrations(bind=engine) -> None:
    """Añade columnas nuevas a tablas ya existentes.

    ``Base.metadata.create_all`` crea las tablas que faltan, pero **no** añade
    columnas a tablas ya creadas. Para no obligar a borrar ``cinema.db``, aquí
    se comprueban y añaden las columnas nuevas que hayan surgido. El código
    específico de cada motor (PRAGMA en SQLite, ALTER COLUMN en PostgreSQL)
    se ejecuta solo en el motor correspondiente.
    """
    inspector = inspect(bind)
    dialect = bind.dialect.name
    table_names = inspector.get_table_names()

    if "movies" in table_names:
        columns = {col["name"] for col in inspector.get_columns("movies")}
        if "poster_url" not in columns:
            with bind.begin() as conn:
                conn.execute(text("ALTER TABLE movies ADD COLUMN poster_url VARCHAR(500)"))

    if "users" in table_names:
        user_columns = {col["name"]: col for col in inspector.get_columns("users")}
        with bind.begin() as conn:
            if "oauth_provider" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20)"))
            if "oauth_id" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(100)"))

            if dialect == "postgresql":
                # En PostgreSQL se puede quitar el NOT NULL sin recrear la tabla.
                hashed = user_columns.get("hashed_password")
                if hashed and not hashed["nullable"]:
                    conn.execute(
                        text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL")
                    )
            elif dialect == "sqlite":
                # SQLite no permite ALTER COLUMN: se edita el esquema en caliente.
                try:
                    conn.execute(text("PRAGMA writable_schema=1"))
                    conn.execute(
                        text(
                            "UPDATE sqlite_master SET sql=replace(sql,"
                            "'hashed_password VARCHAR(255) NOT NULL',"
                            "'hashed_password VARCHAR(255)') "
                            "WHERE type='table' AND name='users'"
                        )
                    )
                    conn.execute(text("PRAGMA writable_schema=0"))
                except Exception:
                    pass
