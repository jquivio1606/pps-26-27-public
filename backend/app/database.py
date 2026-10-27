"""Configuración de la base de datos (SQLite + SQLAlchemy 2.0).

Se usa SQLite para que la API sea ejecutable de inmediato sin dependencias
externas. Para cambiar de motor (PostgreSQL, MySQL, ...) basta con modificar
la variable de entorno ``DATABASE_URL``.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
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
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE}")

# ``check_same_thread`` solo es necesario para SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

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
    se comprueban y añaden las columnas nuevas que hayan surgido.
    """
    inspector = inspect(bind)
    table_names = inspector.get_table_names()

    if "movies" in table_names:
        columns = {col["name"] for col in inspector.get_columns("movies")}
        if "poster_url" not in columns:
            with bind.begin() as conn:
                conn.execute(text("ALTER TABLE movies ADD COLUMN poster_url VARCHAR(500)"))

    if "users" in table_names:
        columns = {col["name"] for col in inspector.get_columns("users")}
        with bind.begin() as conn:
            if "oauth_provider" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20)"))
            if "oauth_id" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(100)"))
            # Make hashed_password nullable if it isn't
            try:
                conn.execute(text("PRAGMA writable_schema=1"))
                conn.execute(text("UPDATE sqlite_master SET sql=replace(sql,'hashed_password VARCHAR(255) NOT NULL','hashed_password VARCHAR(255)') WHERE type='table' AND name='users'"))
                conn.execute(text("PRAGMA writable_schema=0"))
            except Exception:
                pass
