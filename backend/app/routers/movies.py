"""Endpoints del módulo de Películas (Movies)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import require_staff
from ..database import get_db
from ..models import Movie, Showtime, Ticket, User
from ..pagination import Page, PageParams, paginate
from ..schemas import MovieCreate, MovieRead

router = APIRouter(prefix="/movies", tags=["Películas"])


@router.get("", response_model=Page[MovieRead], summary="Listar películas (paginado)")
def list_movies(
    params: PageParams = Depends(), db: Session = Depends(get_db)
) -> dict:
    """Devuelve todas las películas en cartelera de forma paginada.

    Parámetros: ``?page=`` (desde 1) y ``?size=`` (1-100, por defecto 10).
    """
    stmt = select(Movie).order_by(Movie.id)
    return paginate(db, stmt, params)


@router.post(
    "",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir una nueva película (manager o admin)",
)
def create_movie(
    payload: MovieCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> Movie:
    """Registra una nueva película. **Requiere rol manager o admin.**"""
    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@router.get("/{movie_id}", response_model=MovieRead, summary="Obtener una película por ID")
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> Movie:
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    return movie


@router.put(
    "/{movie_id}",
    response_model=MovieRead,
    summary="Modificar una película (manager o admin)",
)
def update_movie(
    movie_id: int,
    payload: MovieCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> Movie:
    """Actualiza los datos de una película. **Requiere rol manager o admin.**"""
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    for field, value in payload.model_dump().items():
        setattr(movie, field, value)

    db.commit()
    db.refresh(movie)
    return movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una película (manager o admin)",
)
def delete_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Elimina una película y sus funciones. **Requiere rol manager o admin.**

    Para no romper el historial de ventas, no se permite eliminar una película
    que tenga entradas vendidas (``409``): primero hay que cancelar (eliminar)
    esas funciones.
    """
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    sold = (
        db.scalar(
            select(func.count())
            .select_from(Ticket)
            .join(Showtime, Ticket.showtime_id == Showtime.id)
            .where(Showtime.movie_id == movie_id)
        )
        or 0
    )
    if sold:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No se puede eliminar: la película tiene entradas vendidas. "
                "Elimina antes sus funciones."
            ),
        )

    db.delete(movie)
    db.commit()

