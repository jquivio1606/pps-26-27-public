"""Punto de entrada principal de la API de cine.

Documentación interactiva:
    * Swagger UI  -> http://127.0.0.1:8000/docs
    * ReDoc       -> http://127.0.0.1:8000/redoc
    * OpenAPI JSON-> http://127.0.0.1:8000/openapi.json

Ejecutar en desarrollo (desde la carpeta ``backend/``):
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .auth import ensure_passwords_encrypted
from .database import Base, SessionLocal, engine, run_light_migrations
from .routers import auth, movies, showtimes, stats, tickets
from .seats import reconcile_reserved_seats
from .seed import seed_db

# El frontend (React + Vite) vive junto a ``backend/`` (raíz del proyecto).
# main.py -> app/ -> backend/ -> raíz del proyecto
# Vite compila la app en ``frontend/dist``; si aún no se ha compilado, se
# sirve el directorio ``frontend`` (útil para no romper el arranque).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SOURCE_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_SOURCE_DIR / "dist"
FRONTEND_DIR = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.is_dir() else FRONTEND_SOURCE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas y carga los datos de prueba al arrancar la app."""
    Base.metadata.create_all(bind=engine)
    # Añade columnas nuevas a tablas ya existentes (sin borrar datos).
    run_light_migrations(engine)
    with SessionLocal() as db:
        seed_db(db)
        # Cifra (bcrypt) cualquier clave que hubiera quedado en texto plano.
        ensure_passwords_encrypted(db)
        # Alinea las butacas reservadas con el aforo (bases de datos antiguas).
        reconcile_reserved_seats(db)
    yield


app = FastAPI(
    title="Cinema API 🎬",
    description=(
        "API REST para gestionar la compra de entradas de cine.\n\n"
        "Módulos: **Autenticación** (JWT), **Películas**, **Funciones**, "
        "**Reservas** y **Estadísticas**.\n\n"
        "Incluye datos de prueba (20 películas y 10 funciones) y tres usuarios:\n\n"
        "* admin / `admin123` (informático: usuarios, roles, claves y sistema)\n"
        "* manager / `manager123` (jefe: catálogo y panel de estadísticas)\n"
        "* user / `user123` (cliente: comprar entradas)\n\n"
        "Las claves se almacenan siempre hasheadas con bcrypt (nunca en claro).\n\n"
        "Los listados están paginados con los parámetros `?page=` y `?size=`."
    ),
    version=__version__,
    lifespan=lifespan,
    contact={"name": "Cinema API", "url": "https://example.com"},
    license_info={"name": "MIT"},
)

# Permite probar la API desde cualquier origen (Postman, front-ends, etc.).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers por módulo.
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(showtimes.router)
app.include_router(tickets.router)
app.include_router(stats.router)


@app.get("/api", tags=["Estado"], summary="Información de la API")
def api_info() -> dict:
    """Endpoint informativo con la versión y enlaces a la documentación."""
    return {
        "app": "Cinema API",
        "version": __version__,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "frontend": "/",
    }


@app.get("/health", tags=["Estado"], summary="Health check")
def health() -> dict:
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
#  Frontend (SPA servida como estáticos). Se monta al final para que las rutas
#  de la API tengan prioridad. Accesible en http://127.0.0.1:8000/
# --------------------------------------------------------------------------- #
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
