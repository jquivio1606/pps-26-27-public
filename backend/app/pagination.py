"""Utilidades de paginación reutilizables por todos los listados.

Uso en un endpoint::

    @router.get("", response_model=Page[MovieRead])
    def list_movies(params: PageParams = Depends(), db: Session = Depends(get_db)):
        stmt = select(Movie).order_by(Movie.id)
        return paginate(db, stmt, params)
"""

from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

T = TypeVar("T")


class PageParams:
    """Parámetros de paginación comunes: ``?page=`` y ``?size=``."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Número de página (empieza en 1)")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Elementos por página (1-100)")] = 10,
    ) -> None:
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
        self.limit = size


class Page(BaseModel, Generic[T]):
    """Envoltorio genérico de respuesta paginada."""

    items: list[T]
    total: int = Field(..., description="Total de elementos")
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Elementos por página")
    pages: int = Field(..., description="Número total de páginas")
    has_next: bool
    has_prev: bool


def paginate(db: Session, stmt: Select, params: PageParams) -> dict:
    """Ejecuta ``stmt`` paginado y devuelve un diccionario compatible con ``Page``.

    El total se calcula sobre la misma consulta (sin orden ni límites) para que
    funcione con cualquier filtro aplicado.
    """
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0

    items = list(
        db.execute(stmt.offset(params.offset).limit(params.limit)).scalars().all()
    )

    pages = ceil(total / params.size) if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": pages,
        "has_next": params.page < pages,
        "has_prev": params.page > 1,
    }
