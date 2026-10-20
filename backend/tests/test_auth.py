"""Pruebas funcionales del módulo de Autenticación."""

import re

import jwt

from app.auth import ALGORITHM, SECRET_KEY
from app.models import User


def test_health_y_api_info(client):
    assert client.get("/health").json() == {"status": "ok"}
    info = client.get("/api").json()
    assert info["docs"] == "/docs"
    assert info["frontend"] == "/"


def test_frontend_se_sirve_en_la_raiz(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "CINE" in resp.text.upper()


def test_assets_del_frontend_disponibles(client):
    html = client.get("/").text
    assets = re.findall(r'/(?:assets|src)/[^"\')\s]+', html)
    assert assets, "El index.html del frontend no referencia ningún asset"
    for path in assets:
        resp = client.get(path)
        assert resp.status_code == 200, f"Asset del frontend no disponible: {path}"


def test_login_correcto_devuelve_token_bearer(client):
    resp = client.post("/auth/login", data={"username": "user", "password": "user123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_con_password_incorrecta(client):
    resp = client.post("/auth/login", data={"username": "user", "password": "malo"})
    assert resp.status_code == 401


def test_login_con_usuario_inexistente(client):
    resp = client.post("/auth/login", data={"username": "nadie", "password": "x"})
    assert resp.status_code == 401


def test_login_sin_datos_devuelve_422(client):
    assert client.post("/auth/login", data={}).status_code == 422


def test_me_con_token_valido(client, user_headers):
    resp = client.get("/auth/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"
    assert resp.json()["role"] == "user"


def test_me_sin_token_devuelve_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token_invalido_devuelve_401(client):
    headers = {"Authorization": "Bearer esto.no.es.un.jwt"}
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_me_con_token_de_usuario_inexistente_devuelve_401(client):
    token = jwt.encode(
        {"sub": "99999", "username": "fantasma", "role": "user"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_register_crea_usuario_con_rol_user(client):
    resp = client.post(
        "/auth/register",
        json={"username": "nuevo", "email": "nuevo@example.com", "password": "clave123"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["role"] == "user"
    assert "hashed_password" not in body and "password" not in body


def test_register_permite_hacer_login(client):
    client.post(
        "/auth/register",
        json={"username": "nuevo", "email": "nuevo@example.com", "password": "clave123"},
    )
    resp = client.post("/auth/login", data={"username": "nuevo", "password": "clave123"})
    assert resp.status_code == 200


def test_register_usuario_duplicado(client):
    payload = {"username": "dup", "email": "dup@example.com", "password": "clave123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_register_email_duplicado(client):
    assert client.post(
        "/auth/register",
        json={"username": "usera", "email": "repe@example.com", "password": "clave123"},
    ).status_code == 201
    assert client.post(
        "/auth/register",
        json={"username": "userb", "email": "repe@example.com", "password": "clave123"},
    ).status_code == 409


def test_register_password_corta_devuelve_422(client):
    resp = client.post(
        "/auth/register",
        json={"username": "corto", "email": "corto@example.com", "password": "123"},
    )
    assert resp.status_code == 422


def test_register_email_invalido_devuelve_422(client):
    resp = client.post(
        "/auth/register",
        json={"username": "malo", "email": "no-es-un-email", "password": "clave123"},
    )
    assert resp.status_code == 422
