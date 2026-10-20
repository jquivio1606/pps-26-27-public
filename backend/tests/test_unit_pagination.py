"""Pruebas unitarias del módulo de paginación."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Movie
from app.pagination import PageParams, paginate


def test_pageparams_calcula_offset_y_limite():
    p = PageParams(page=3, size=20)
    assert (p.page, p.size, p.offset, p.limit) == (3, 20, 40, 20)


def test_pageparams_valores_por_defecto():
    p = PageParams()
    assert (p.page, p.size, p.offset, p.limit) == (1, 10, 0, 10)


def test_pageparams_primera_pagina_no_tiene_offset():
    assert PageParams(page=1, size=5).offset == 0


def test_paginate_devuelve_metadatos_correctos(client):
    with SessionLocal() as db:
        page = paginate(db, select(Movie).order_by(Movie.id), PageParams(page=1, size=10))
    assert page["total"] == 20
    assert len(page["items"]) == 10
    assert page["pages"] == 2
    assert page["has_next"] is True
    assert page["has_prev"] is False


def test_paginate_ultima_pagina(client):
    with SessionLocal() as db:
        page = paginate(db, select(Movie).order_by(Movie.id), PageParams(page=2, size=10))
    assert len(page["items"]) == 10
    assert page["has_next"] is False
    assert page["has_prev"] is True


def test_paginate_pagina_vacia_pero_valida(client):
    with SessionLocal() as db:
        page = paginate(db, select(Movie).order_by(Movie.id), PageParams(page=99, size=10))
    assert page["items"] == []
    assert page["total"] == 20


def test_paginate_respeta_filtros_en_el_total(client):
    with SessionLocal() as db:
        stmt = select(Movie).where(Movie.genre == "Animación").order_by(Movie.id)
        page = paginate(db, stmt, PageParams(page=1, size=50))
    assert page["total"] == len(page["items"]) > 0
