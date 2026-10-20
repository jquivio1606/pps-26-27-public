"""Prueba funcional (caja negra) contra un servidor REAL en marcha.

No usa el cliente de pruebas de FastAPI: hace peticiones HTTP reales, así que
valida uvicorn, el enrutado, CORS y la serialización tal cual los verá Postman.

Uso:
    1. Arranca el servidor:  start.bat   (o, desde backend/, uvicorn app.main:app)
    2. En otra terminal:      python backend/tests/live_check.py

Puedes apuntar a otro host con la variable de entorno BASE_URL.
"""

import os
import sys

import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
ok = 0
failed = 0


def check(descripcion: str, condicion: bool, detalle: str = "") -> None:
    global ok, failed
    if condicion:
        ok += 1
        print(f"  [OK]   {descripcion}")
    else:
        failed += 1
        print(f"  [FALLO] {descripcion} {detalle}")


def login(client: httpx.Client, username: str, password: str) -> dict:
    resp = client.post("/auth/login", data={"username": username, "password": password})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def main() -> int:
    print(f"Pruebas funcionales contra {BASE_URL}\n")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    print("Estado:")
    check("GET /health responde ok", client.get("/health").json() == {"status": "ok"})
    check("GET /docs responde 200", client.get("/docs").status_code == 200)
    check("GET /openapi.json responde 200", client.get("/openapi.json").status_code == 200)

    print("\nAutenticación:")
    admin = login(client, "admin", "admin123")
    manager = login(client, "manager", "manager123")
    user = login(client, "user", "user123")
    check("login admin devuelve token", "Authorization" in admin)
    check("login manager devuelve token", "Authorization" in manager)
    check("login user devuelve token", "Authorization" in user)
    malas = client.post("/auth/login", data={"username": "admin", "password": "malo"})
    check("login con clave incorrecta -> 401", malas.status_code == 401)
    check("GET /auth/me sin token -> 401", client.get("/auth/me").status_code == 401)
    check("GET /auth/me con token -> 200", client.get("/auth/me", headers=user).status_code == 200)

    print("\nPaginación:")
    movies = client.get("/movies?page=1&size=5").json()
    check("GET /movies?page=1&size=5 -> 5 items", len(movies["items"]) == 5)
    check("total de películas >= 20", movies["total"] >= 20)
    check("metadatos de página presentes", set(["total", "page", "size", "pages", "has_next", "has_prev"]) <= set(movies))

    print("\nPelículas (roles):")
    check(
        "usuario normal no puede crear película -> 403",
        client.post(
            "/movies", headers=user,
            json={"title": "No permitida", "genre": "X", "duration_minutes": 90},
        ).status_code == 403,
    )
    nueva = client.post(
        "/movies", headers=admin,
        json={"title": "Live Check", "genre": "Test", "duration_minutes": 99},
    )
    check("admin crea película -> 201", nueva.status_code == 201, nueva.text)
    movie_id = nueva.json()["id"]

    print("\nRoles y panel de gestión:")
    check(
        "usuario normal no puede modificar película -> 403",
        client.put(
            f"/movies/{movie_id}", headers=user,
            json={"title": "No permitida", "genre": "X", "duration_minutes": 90},
        ).status_code == 403,
    )
    manager_movie = client.post(
        "/movies", headers=manager,
        json={"title": "Live Check manager", "genre": "Test", "duration_minutes": 88},
    )
    check("manager crea película -> 201", manager_movie.status_code == 201, manager_movie.text)
    check(
        "manager modifica película -> 200",
        client.put(
            f"/movies/{manager_movie.json()['id']}", headers=manager,
            json={"title": "Live Check manager v2", "genre": "Test", "duration_minutes": 89},
        ).status_code == 200,
    )
    check(
        "manager elimina su película -> 204",
        client.delete(f"/movies/{manager_movie.json()['id']}", headers=manager).status_code == 204,
    )
    check(
        "usuario normal no ve las estadísticas -> 403",
        client.get("/stats/dashboard", headers=user).status_code == 403,
    )
    stats = client.get("/stats/dashboard", headers=manager)
    check("manager ve las estadísticas -> 200", stats.status_code == 200, stats.text)
    check("las estadísticas incluyen el reparto de roles", "users_by_role" in stats.json())
    check(
        "manager no puede gestionar usuarios -> 403",
        client.get("/auth/users", headers=manager).status_code == 403,
    )
    usuarios = client.get("/auth/users", headers=admin)
    check("admin lista usuarios -> 200", usuarios.status_code == 200, usuarios.text)
    check(
        "las claves nunca se exponen",
        all("hashed_password" not in u and "password" not in u for u in usuarios.json()["items"]),
    )
    check(
        "admin ve la información del sistema -> 200",
        client.get("/stats/system", headers=admin).status_code == 200,
    )
    system = client.get("/stats/system", headers=admin).json()
    tech_names = {t["name"] for t in system.get("technologies", [])}
    check(
        "el sistema lista las tecnologías usadas",
        {"FastAPI", "bcrypt"} <= tech_names,
        str(sorted(tech_names)),
    )
    check(
        "manager no puede ver el sistema -> 403",
        client.get("/stats/system", headers=manager).status_code == 403,
    )

    print("\nFunciones:")
    showtime = client.post(
        "/showtimes", headers=admin,
        json={
            "movie_id": movie_id,
            "room": "Sala Live",
            "start_time": "2026-12-31T20:00:00",
            "total_seats": 40,
            "price": 5.0,
        },
    )
    check("admin crea función -> 201", showtime.status_code == 201, showtime.text)
    sid = showtime.json()["id"]
    check("la función arranca con 40 asientos", showtime.json()["available_seats"] == 40)

    print("\nReservas:")
    check(
        "reserva sin token -> 401",
        client.post(
            "/tickets/book",
            json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1},
        ).status_code == 401,
    )
    compra = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Ana Live", "quantity": 5},
    )
    check("compra válida -> 201", compra.status_code == 201, compra.text)
    check("quedan 35 asientos", compra.json()["remaining_seats"] == 35)
    check("total_price = 5 * 5 = 25", compra.json()["ticket"]["total_price"] == 25.0)

    exceso = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 9999},
    )
    check("compra sin asientos -> 400", exceso.status_code == 400)
    check(
        "el aforo no cambió tras el error",
        client.get(f"/showtimes/{sid}").json()["available_seats"] == 35,
    )
    check(
        "el usuario ve su reserva",
        client.get("/tickets", headers=user).json()["total"] >= 1,
    )

    print("\nSelección de asientos:")
    mapa = client.get(f"/showtimes/{sid}/seats").json()
    check("mapa de asientos -> 40 butacas", mapa.get("total_seats") == 40)
    check(
        "mapa en 4 filas de 10 (A-D)",
        len(mapa["rows"]) == 4
        and mapa["rows"][0]["row"] == "A"
        and len(mapa["rows"][0]["seats"]) == 10,
    )
    check("las 5 butacas de la compra automática están ocupadas", len(mapa["reserved"]) == 5)

    compra_asientos = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 2, "seats": ["B1", "B2"]},
    )
    check("compra con butacas -> 201", compra_asientos.status_code == 201, compra_asientos.text)
    check(
        "devuelve las butacas elegidas",
        sorted(compra_asientos.json()["ticket"]["seats"]) == ["B1", "B2"],
    )
    check("quedan 33 asientos", compra_asientos.json()["remaining_seats"] == 33)

    repetida = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Otra", "quantity": 1, "seats": ["B1"]},
    )
    check("butaca ya ocupada -> 409", repetida.status_code == 409)

    desajuste = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 3, "seats": ["C1", "C2"]},
    )
    check("butacas distintas al nº de entradas -> 400", desajuste.status_code == 400)

    invalida = client.post(
        "/tickets/book", headers=user,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1, "seats": ["Z99"]},
    )
    check("butaca inexistente -> 400", invalida.status_code == 400)

    print("\nCancelación de entradas (gestión):")
    tid1 = compra.json()["ticket"]["id"]
    tid2 = compra_asientos.json()["ticket"]["id"]

    check(
        "usuario normal no puede listar todas las reservas -> 403",
        client.get("/tickets?scope=all", headers=user).status_code == 403,
    )
    todas = client.get("/tickets?scope=all", headers=manager)
    check("manager lista todas las reservas -> 200", todas.status_code == 200, todas.text)
    check("el manager ve las entradas de los clientes", todas.json()["total"] >= 2)

    entradas = {t["id"]: t for t in todas.json()["items"]}
    check(
        "la entrada identifica usuario y función",
        entradas.get(tid2, {}).get("username") == "user"
        and entradas.get(tid2, {}).get("movie_title") == "Live Check"
        and entradas.get(tid2, {}).get("room") == "Sala Live",
        str(entradas.get(tid2)),
    )
    busqueda = client.get("/tickets?scope=all&search=user", headers=manager)
    check("búsqueda por jugador (?search=user) -> 2 entradas", busqueda.json()["total"] == 2)

    check(
        "el cliente no puede cancelar entradas -> 403",
        client.delete(f"/tickets/{tid2}", headers=user).status_code == 403,
    )
    cancelada = client.delete(f"/tickets/{tid2}", headers=manager)
    check("manager cancela la entrada -> 204", cancelada.status_code == 204, cancelada.text)
    check(
        "se liberan las 2 butacas (quedan 35)",
        client.get(f"/showtimes/{sid}").json()["available_seats"] == 35,
    )
    mapa_tras = client.get(f"/showtimes/{sid}/seats").json()
    check(
        "B1 y B2 vuelven a estar libres",
        "B1" not in mapa_tras["reserved"] and "B2" not in mapa_tras["reserved"],
    )
    check(
        "la entrada cancelada desaparece",
        client.get(f"/tickets/{tid2}", headers=manager).status_code == 404
        and client.get("/tickets", headers=user).json()["total"] == 1,
    )
    check(
        "cancelar una reserva inexistente -> 404",
        client.delete("/tickets/999999", headers=manager).status_code == 404,
    )
    check(
        "admin cancela la otra entrada -> 204",
        client.delete(f"/tickets/{tid1}", headers=admin).status_code == 204,
    )
    check(
        "la función queda con el aforo completo",
        client.get(f"/showtimes/{sid}").json()["available_seats"] == 40,
    )
    check(
        "el cliente ya no tiene reservas",
        client.get("/tickets", headers=user).json()["total"] == 0,
    )

    client.close()
    print(f"\nResultado: {ok} OK, {failed} FALLOS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
