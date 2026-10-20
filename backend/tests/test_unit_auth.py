"""Pruebas unitarias de la capa de seguridad (hasheo y JWT)."""

from datetime import timedelta

import jwt
import pytest

from app.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User


def _user(role: str = "user", uid: int = 7) -> User:
    return User(id=uid, username="ana", email="ana@example.com", hashed_password="x", role=role)


def test_hash_password_genera_hash_bcrypt_distinto_del_texto():
    hashed = hash_password("secreto123")
    assert hashed != "secreto123"
    assert hashed.startswith("$2")  # prefijo de bcrypt


def test_hash_password_es_salado_y_verificable():
    h1 = hash_password("secreto123")
    h2 = hash_password("secreto123")
    assert h1 != h2  # salt aleatorio
    assert verify_password("secreto123", h1)
    assert verify_password("secreto123", h2)


def test_verify_password_falla_con_password_incorrecta():
    hashed = hash_password("secreto123")
    assert verify_password("otra-clave", hashed) is False


def test_verify_password_con_hash_invalido_no_lanza_excepcion():
    assert verify_password("x", "esto-no-es-un-hash") is False


def test_create_access_token_incluye_claims_esperados():
    token = create_access_token(_user(role="admin", uid=42))
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "42"
    assert payload["username"] == "ana"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_create_access_token_expira():
    token = create_access_token(_user(), expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def test_token_firmado_con_otra_clave_es_rechazado():
    token = create_access_token(_user())
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "otra-clave-distinta", algorithms=[ALGORITHM])
