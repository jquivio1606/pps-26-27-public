"""Pruebas de los pósters: catálogo, migración ligera y relleno en bases existentes."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Movie
from app.seed import MOVIES, POSTERS_BY_TITLE, backfill_posters


def test_el_catalogo_tiene_poster_para_las_20_peliculas():
    assert len(MOVIES) == 20
    assert all(m.get("poster_url") for m in MOVIES)
    assert len(POSTERS_BY_TITLE) == 20


def test_backfill_rellena_el_poster_faltante(client):
    with SessionLocal() as db:
        movie = db.scalar(select(Movie).where(Movie.title == "Origen"))
        movie.poster_url = None
        db.commit()

    with SessionLocal() as db:
        backfill_posters(db)

    with SessionLocal() as db:
        movie = db.scalar(select(Movie).where(Movie.title == "Origen"))
        assert movie.poster_url == POSTERS_BY_TITLE["Origen"]


def test_backfill_respeta_peliculas_personalizadas(client):
    with SessionLocal() as db:
        movie = Movie(title="Personalizada", genre="Drama", duration_minutes=90)
        db.add(movie)
        db.commit()
        movie_id = movie.id

    with SessionLocal() as db:
        backfill_posters(db)

    with SessionLocal() as db:
        assert db.get(Movie, movie_id).poster_url is None
