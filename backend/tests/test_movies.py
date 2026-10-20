"""Pruebas funcionales del módulo de Películas."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Movie


def test_listar_peliculas_paginado(client):
    resp = client.get("/movies")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 20
    assert len(body["items"]) == 10  # tamaño por defecto
    assert body["pages"] == 2
    assert body["has_next"] and not body["has_prev"]


def test_paginacion_no_solapa_paginas(client):
    p1 = client.get("/movies?page=1&size=5").json()
    p2 = client.get("/movies?page=2&size=5").json()
    ids1 = {m["id"] for m in p1["items"]}
    ids2 = {m["id"] for m in p2["items"]}
    assert len(ids1) == 5 and len(ids2) == 5
    assert ids1.isdisjoint(ids2)


def test_paginacion_size_fuera_de_rango(client):
    assert client.get("/movies?size=0").status_code == 422
    assert client.get("/movies?size=101").status_code == 422
    assert client.get("/movies?page=0").status_code == 422


def test_obtener_pelicula_por_id(client):
    movie_id = client.get("/movies?size=1").json()["items"][0]["id"]
    resp = client.get(f"/movies/{movie_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == movie_id


def test_obtener_pelicula_inexistente_devuelve_404(client):
    assert client.get("/movies/999999").status_code == 404


def test_crear_pelicula_como_admin(client, admin_headers):
    resp = client.post(
        "/movies",
        headers=admin_headers,
        json={"title": "Nueva", "genre": "Drama", "duration_minutes": 100},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] > 0
    assert client.get("/movies?size=1").json()["total"] == 21


def test_crear_pelicula_sin_autenticacion(client):
    resp = client.post(
        "/movies", json={"title": "X", "genre": "Y", "duration_minutes": 90}
    )
    assert resp.status_code == 401


def test_crear_pelicula_como_usuario_normal_prohibido(client, user_headers):
    resp = client.post(
        "/movies",
        headers=user_headers,
        json={"title": "X", "genre": "Y", "duration_minutes": 90},
    )
    assert resp.status_code == 403


def test_crear_pelicula_con_duracion_invalida(client, admin_headers):
    resp = client.post(
        "/movies",
        headers=admin_headers,
        json={"title": "X", "genre": "Y", "duration_minutes": 0},
    )
    assert resp.status_code == 422


def test_crear_pelicula_sin_titulo(client, admin_headers):
    resp = client.post(
        "/movies", headers=admin_headers, json={"genre": "Y", "duration_minutes": 90}
    )
    assert resp.status_code == 422


def test_las_peliculas_sembradas_tienen_poster(client):
    body = client.get("/movies?size=100").json()
    con_poster = [m for m in body["items"] if m["poster_url"]]
    assert len(con_poster) == 20
    assert all(m["poster_url"].startswith("https://") for m in con_poster)


def test_crear_pelicula_con_poster(client, admin_headers):
    resp = client.post(
        "/movies",
        headers=admin_headers,
        json={
            "title": "Con póster",
            "genre": "Drama",
            "duration_minutes": 100,
            "poster_url": "https://example.com/poster.jpg",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["poster_url"] == "https://example.com/poster.jpg"


def test_crear_pelicula_sin_poster_queda_vacio(client, admin_headers):
    resp = client.post(
        "/movies",
        headers=admin_headers,
        json={"title": "Sin póster", "genre": "Drama", "duration_minutes": 100},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["poster_url"] is None


def test_poster_demasiado_largo_devuelve_422(client, admin_headers):
    resp = client.post(
        "/movies",
        headers=admin_headers,
        json={
            "title": "Largo",
            "genre": "Drama",
            "duration_minutes": 100,
            "poster_url": "https://example.com/" + "x" * 500,
        },
    )
    assert resp.status_code == 422


def test_eliminar_pelicula_como_admin(client, admin_headers):
    movie_id = client.get("/movies?size=1").json()["items"][0]["id"]
    assert client.delete(f"/movies/{movie_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/movies/{movie_id}").status_code == 404
    assert client.get("/movies?size=1").json()["total"] == 19


def test_eliminar_pelicula_como_usuario_prohibido(client, user_headers):
    movie_id = client.get("/movies?size=1").json()["items"][0]["id"]
    assert client.delete(f"/movies/{movie_id}", headers=user_headers).status_code == 403


def test_eliminar_pelicula_inexistente(client, admin_headers):
    assert client.delete("/movies/999999", headers=admin_headers).status_code == 404


def test_eliminar_pelicula_borra_sus_funciones(client, admin_headers):
    with SessionLocal() as db:
        movie_id = db.execute(select(Movie).where(Movie.title == "Origen")).scalar_one().id

    showtime_ids = [
        s["id"] for s in client.get(f"/showtimes?movie_id={movie_id}&size=100").json()["items"]
    ]
    assert showtime_ids, "la película debería tener funciones de prueba"

    client.delete(f"/movies/{movie_id}", headers=admin_headers)

    for showtime_id in showtime_ids:
        assert client.get(f"/showtimes/{showtime_id}").status_code == 404
