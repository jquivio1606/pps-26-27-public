"""Pruebas de roles (user / manager / admin), claves cifradas y estadísticas.

Reparte las responsabilidades pedidas:

* ``manager`` (jefe): puede añadir, modificar y eliminar catálogo (películas y
  funciones) y ver el panel de estadísticas, pero no toca usuarios ni sistema.
* ``admin`` (informático): además de lo anterior, gestiona usuarios, roles y
  claves, y consulta la información técnica del sistema.
* ``user`` (cliente): igual que antes, sin ningún permiso de gestión.
"""

from sqlalchemy import select

from app.auth import ensure_passwords_encrypted, is_hashed_password
from app.database import SessionLocal
from app.models import User


# --------------------------------------------------------------------------- #
#  El jefe (manager) puede gestionar el catálogo
# --------------------------------------------------------------------------- #
def test_manager_puede_crear_pelicula(client, manager_headers):
    resp = client.post(
        "/movies",
        headers=manager_headers,
        json={"title": "Del jefe", "genre": "Drama", "duration_minutes": 100},
    )
    assert resp.status_code == 201, resp.text


def test_manager_puede_modificar_pelicula(client, manager_headers):
    resp = client.put(
        "/movies/1",
        headers=manager_headers,
        json={"title": "El Padrino (remaster)", "genre": "Drama", "duration_minutes": 180},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "El Padrino (remaster)"
    assert resp.json()["duration_minutes"] == 180


def test_modificar_pelicula_inexistente_devuelve_404(client, manager_headers):
    resp = client.put(
        "/movies/999999",
        headers=manager_headers,
        json={"title": "X", "genre": "Y", "duration_minutes": 90},
    )
    assert resp.status_code == 404


def test_usuario_no_puede_modificar_pelicula(client, user_headers):
    resp = client.put(
        "/movies/1",
        headers=user_headers,
        json={"title": "X", "genre": "Y", "duration_minutes": 90},
    )
    assert resp.status_code == 403


def test_manager_puede_eliminar_pelicula_sin_reservas(client, manager_headers):
    assert client.delete("/movies/1", headers=manager_headers).status_code == 204


def test_manager_no_puede_eliminar_pelicula_con_reservas(client, manager_headers, user_headers):
    showtime_id = client.get("/showtimes/1").json()["id"]
    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": showtime_id, "customer_name": "Ana", "quantity": 1},
        ).status_code
        == 201
    )
    resp = client.delete("/movies/1", headers=manager_headers)
    assert resp.status_code == 409
    assert "entradas vendidas" in resp.json()["detail"]


# --------------------------------------------------------------------------- #
#  El jefe (manager) puede gestionar las funciones
# --------------------------------------------------------------------------- #
def test_manager_puede_modificar_funcion(client, manager_headers):
    resp = client.put(
        "/showtimes/1",
        headers=manager_headers,
        json={"room": "Sala VIP", "price": 12.0},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["room"] == "Sala VIP"
    assert resp.json()["price"] == 12.0


def test_modificar_funcion_recalcula_asientos_disponibles(client, manager_headers, user_headers):
    # Se venden 3 butacas y luego se cambia el aforo: disponibles = aforo - vendidas.
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 1, "customer_name": "Ana", "quantity": 3},
    )
    resp = client.put("/showtimes/1", headers=manager_headers, json={"total_seats": 50})
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_seats"] == 50
    assert resp.json()["available_seats"] == 47


def test_no_se_puede_reducir_el_aforo_por_debajo_de_las_vendidas(client, manager_headers, user_headers):
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 1, "customer_name": "Ana", "quantity": 4},
    )
    resp = client.put("/showtimes/1", headers=manager_headers, json={"total_seats": 3})
    assert resp.status_code == 400


def test_manager_puede_eliminar_funcion_sin_reservas(client, manager_headers):
    assert client.delete("/showtimes/1", headers=manager_headers).status_code == 204
    assert client.get("/showtimes/1").status_code == 404


def test_no_se_puede_eliminar_funcion_con_reservas(client, manager_headers, user_headers):
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 1, "customer_name": "Ana", "quantity": 1},
    )
    resp = client.delete("/showtimes/1", headers=manager_headers)
    assert resp.status_code == 409


def test_usuario_no_puede_eliminar_funcion(client, user_headers):
    assert client.delete("/showtimes/1", headers=user_headers).status_code == 403


# --------------------------------------------------------------------------- #
#  Estadísticas de la web (manager y admin)
# --------------------------------------------------------------------------- #
def test_manager_ve_estadisticas(client, manager_headers):
    resp = client.get("/stats/dashboard", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["movies"] == 20
    assert body["showtimes"] == 10
    assert body["users"] == 3
    assert set(body["users_by_role"]) == {"user", "manager", "admin"}
    assert body["users_by_role"]["admin"] == 1
    assert body["top_movies"]


def test_usuario_no_ve_las_estadisticas(client, user_headers):
    assert client.get("/stats/dashboard", headers=user_headers).status_code == 403


def test_estadisticas_reflejan_las_ventas(client, manager_headers, user_headers):
    precio = client.get("/showtimes/1").json()["price"]
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 1, "customer_name": "Ana", "quantity": 2},
    )
    body = client.get("/stats/dashboard", headers=manager_headers).json()
    assert body["tickets"] == 1
    assert body["seats_sold"] == 2
    assert body["revenue"] == round(2 * precio, 2)
    assert body["recent_tickets"][0]["quantity"] == 2
    assert body["occupancy_percent"] > 0


def test_ocupacion_calculada_sobre_el_aforo_total(client, manager_headers):
    showtimes = client.get("/showtimes?size=100").json()["items"]
    assert client.get("/stats/dashboard", headers=manager_headers).json()["seats_total"] == sum(
        s["total_seats"] for s in showtimes
    )


# --------------------------------------------------------------------------- #
#  Gestión de usuarios y sistema (solo admin)
# --------------------------------------------------------------------------- #
def test_admin_lista_usuarios(client, admin_headers):
    resp = client.get("/auth/users", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert {u["username"] for u in body["items"]} == {"admin", "manager", "user"}
    assert all("hashed_password" not in u for u in body["items"])


def test_listar_usuarios_con_filtro_de_rol(client, admin_headers):
    body = client.get("/auth/users?role=manager", headers=admin_headers).json()
    assert body["total"] == 1
    assert body["items"][0]["username"] == "manager"


def test_manager_no_puede_gestionar_usuarios(client, manager_headers):
    assert client.get("/auth/users", headers=manager_headers).status_code == 403
    assert client.get("/stats/system", headers=manager_headers).status_code == 403


def test_usuario_no_puede_gestionar_usuarios(client, user_headers):
    assert client.get("/auth/users", headers=user_headers).status_code == 403


def test_admin_cambia_el_rol_de_un_usuario(client, admin_headers):
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    resp = client.patch(f"/auth/users/{user_id}", headers=admin_headers, json={"role": "manager"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "manager"
    assert client.post("/auth/login", data={"username": "user", "password": "user123"}).status_code == 200


def test_admin_cambia_el_email_de_un_usuario(client, admin_headers):
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    resp = client.patch(
        f"/auth/users/{user_id}", headers=admin_headers, json={"email": "nuevo@cinema.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "nuevo@cinema.com"


def test_rol_invalido_devuelve_422(client, admin_headers):
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    assert (
        client.patch(f"/auth/users/{user_id}", headers=admin_headers, json={"role": "root"}).status_code
        == 422
    )


def test_no_se_puede_quitar_el_rol_al_ultimo_admin(client, admin_headers):
    admin_id = client.get("/auth/users?role=admin", headers=admin_headers).json()["items"][0]["id"]
    resp = client.patch(f"/auth/users/{admin_id}", headers=admin_headers, json={"role": "user"})
    assert resp.status_code == 409


def test_admin_no_puede_eliminar_su_propia_cuenta(client, admin_headers):
    admin_id = client.get("/auth/users?role=admin", headers=admin_headers).json()["items"][0]["id"]
    assert client.delete(f"/auth/users/{admin_id}", headers=admin_headers).status_code == 400


def test_admin_puede_restablecer_la_clave(client, admin_headers):
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    resp = client.post(
        f"/auth/users/{user_id}/password",
        headers=admin_headers,
        json={"password": "nuevaClave99"},
    )
    assert resp.status_code == 200, resp.text
    assert client.post("/auth/login", data={"username": "user", "password": "user123"}).status_code == 401
    assert client.post("/auth/login", data={"username": "user", "password": "nuevaClave99"}).status_code == 200


def test_admin_puede_eliminar_un_usuario(client, admin_headers):
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    assert client.delete(f"/auth/users/{user_id}", headers=admin_headers).status_code == 204
    assert client.get("/auth/users", headers=admin_headers).json()["total"] == 2
    assert client.post("/auth/login", data={"username": "user", "password": "user123"}).status_code == 401


def test_eliminar_usuario_con_reservas_conserva_el_historial(client, admin_headers, user_headers):
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 1, "customer_name": "Ana", "quantity": 1},
    )
    user_id = client.get("/auth/users?role=user", headers=admin_headers).json()["items"][0]["id"]
    assert client.delete(f"/auth/users/{user_id}", headers=admin_headers).status_code == 204
    # La reserva sigue existiendo (ahora sin usuario asociado).
    assert client.get("/tickets", headers=admin_headers).json()["total"] == 1


def test_admin_ve_la_informacion_del_sistema(client, admin_headers):
    resp = client.get("/stats/system", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["password_hashing"] == "bcrypt"
    assert body["users_total"] == 3
    assert body["users_hashed"] == 3
    assert body["secret_key_configured"] is True  # conftest define SECRET_KEY
    assert "secret" not in str(body).lower().replace("secret_key_configured", "")
    assert body["tables"]["movies"] == 20


def test_el_sistema_lista_las_tecnologias(client, admin_headers):
    body = client.get("/stats/system", headers=admin_headers).json()
    techs = body["technologies"]
    assert techs, "debe informar de las tecnologías usadas"
    names = {t["name"] for t in techs}
    # Pila real del proyecto: servidor, datos y seguridad.
    assert {"Python", "FastAPI", "SQLAlchemy", "bcrypt"} <= names
    assert any(t["group"] == "Seguridad" for t in techs)
    for tech in techs:
        assert tech["purpose"], f"{tech['name']} debe indicar para qué se usa"
        assert "secret" not in tech["name"].lower()


# --------------------------------------------------------------------------- #
#  Las claves de usuario nunca se guardan en claro
# --------------------------------------------------------------------------- #
def test_registro_guarda_la_clave_hasheada(client):
    client.post(
        "/auth/register",
        json={"username": "ana", "email": "ana@example.com", "password": "secreto123"},
    )
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.username == "ana")).scalar_one()
    assert user.hashed_password != "secreto123"
    assert is_hashed_password(user.hashed_password)


def test_las_claves_sembradas_estan_hasheadas(client):
    with SessionLocal() as db:
        users = db.scalars(select(User)).all()
    assert users
    assert all(is_hashed_password(u.hashed_password) for u in users)


def test_migracion_cifra_claves_antiguas_en_texto_plano(client):
    with SessionLocal() as db:
        db.add(
            User(
                username="legacy",
                email="legacy@example.com",
                hashed_password="claveEnClaro",
                role="user",
            )
        )
        db.commit()
        assert ensure_passwords_encrypted(db) == 1
        user = db.execute(select(User).where(User.username == "legacy")).scalar_one()
        assert is_hashed_password(user.hashed_password)
        assert user.hashed_password != "claveEnClaro"

    # La cuenta sigue pudiendo iniciar sesión con su clave original.
    assert (
        client.post("/auth/login", data={"username": "legacy", "password": "claveEnClaro"}).status_code
        == 200
    )
