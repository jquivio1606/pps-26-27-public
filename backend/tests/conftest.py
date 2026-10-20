"""Configuración compartida de las pruebas.

Antes de importar la aplicación se apunta ``DATABASE_URL`` a un fichero SQLite
temporal para no tocar la base de datos real (``cinema.db``). Cada test arranca
con la base de datos recién sembrada (2 usuarios, 20 películas, 10 funciones).
"""

import os
import pathlib
import tempfile

_TEST_DB = pathlib.Path(tempfile.gettempdir()) / "cinema_pytest.db"
for _suffix in ("", "-journal", "-wal", "-shm"):
    _p = pathlib.Path(str(_TEST_DB) + _suffix)
    if _p.exists():
        _p.unlink()

os.environ["DATABASE_URL"] = "sqlite:///" + _TEST_DB.as_posix()
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_db  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP de pruebas (ejecuta el lifespan: crea tablas y siembra)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_db(client):
    """Aísla cada test: base de datos vacía y recién sembrada."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_db(db)
    yield


def _auth_headers(client: TestClient, username: str, password: str) -> dict:
    resp = client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin_headers(client) -> dict:
    return _auth_headers(client, "admin", "admin123")


@pytest.fixture
def user_headers(client) -> dict:
    return _auth_headers(client, "user", "user123")


@pytest.fixture
def manager_headers(client) -> dict:
    return _auth_headers(client, "manager", "manager123")
