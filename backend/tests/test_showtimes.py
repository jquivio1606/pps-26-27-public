"""Pruebas funcionales del módulo de Funciones (Showtimes)."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Movie


def _first_movie_id(client) -> int:
    return client.get("/movies?size=1").json()["items"][0]["id"]


def test_listar_funciones_paginado(client):
    resp = client.get("/showtimes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 10
    assert len(body["items"]) == 10
    assert body["pages"] == 1


def test_funciones_incluyen_datos_de_la_pelicula(client):
    item = client.get("/showtimes?size=1").json()["items"][0]
    assert item["movie"] is not None
    assert item["movie"]["title"]


def test_filtrar_funciones_por_pelicula(client):
    with SessionLocal() as db:
        movie_id = db.execute(select(Movie).where(Movie.title == "Origen")).scalar_one().id

    body = client.get(f"/showtimes?movie_id={movie_id}&size=100").json()
    assert body["total"] >= 1
    assert all(s["movie_id"] == movie_id for s in body["items"])


def test_crear_funcion_como_admin_inicializa_asientos(client, admin_headers):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 60,
            "price": 7.5,
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["available_seats"] == 60  # sin indicarlo -> igual al total
    assert body["price"] == 7.5


def test_crear_funcion_con_asientos_disponibles_explicitos(client, admin_headers):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 60,
            "available_seats": 40,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["available_seats"] == 40


def test_crear_funcion_con_pelicula_inexistente(client, admin_headers):
    resp = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": 999999,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 60,
        },
    )
    assert resp.status_code == 404


def test_crear_funcion_con_mas_asientos_disponibles_que_totales(client, admin_headers):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 50,
            "available_seats": 999,
        },
    )
    assert resp.status_code == 400


def test_crear_funcion_sin_autenticacion(client):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 50,
        },
    )
    assert resp.status_code == 401


def test_crear_funcion_como_usuario_prohibido(client, user_headers):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        headers=user_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 50,
        },
    )
    assert resp.status_code == 403


def test_crear_funcion_con_aforo_invalido(client, admin_headers):
    movie_id = _first_movie_id(client)
    resp = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala 9",
            "start_time": "2026-11-01T20:00:00",
            "total_seats": 0,
        },
    )
    assert resp.status_code == 422


def test_obtener_funcion_inexistente(client):
    assert client.get("/showtimes/999999").status_code == 404
