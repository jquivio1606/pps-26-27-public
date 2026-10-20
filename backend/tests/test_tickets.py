"""Pruebas funcionales del módulo de Reservas (Tickets)."""


def _showtime_id(client, index: int = 0) -> int:
    return client.get("/showtimes?size=100").json()["items"][index]["id"]


def _available_seats(client, showtime_id: int) -> int:
    return client.get(f"/showtimes/{showtime_id}").json()["available_seats"]


def test_comprar_requiere_autenticacion(client):
    sid = _showtime_id(client)
    resp = client.post(
        "/tickets/book",
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1},
    )
    assert resp.status_code == 401


def test_compra_correcta_descuenta_asientos(client, user_headers):
    sid = _showtime_id(client)
    antes = _available_seats(client, sid)

    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana López", "quantity": 3},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["remaining_seats"] == antes - 3
    assert body["ticket"]["quantity"] == 3
    assert body["ticket"]["user_id"] is not None
    assert _available_seats(client, sid) == antes - 3


def test_compra_calcula_total_price(client, admin_headers):
    # Función con precio conocido: creamos una a medida para no depender del seed.
    movie_id = client.get("/movies?size=1").json()["items"][0]["id"]
    st = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": movie_id,
            "room": "Sala Test",
            "start_time": "2026-12-01T20:00:00",
            "total_seats": 10,
            "price": 6.25,
        },
    ).json()

    body = client.post(
        "/tickets/book",
        headers=admin_headers,
        json={"showtime_id": st["id"], "customer_name": "Ana", "quantity": 4},
    ).json()
    assert body["ticket"]["total_price"] == 25.0  # 4 * 6.25


def test_compra_sin_asientos_suficientes_devuelve_400_sin_cambios(client, user_headers):
    sid = _showtime_id(client)
    antes = _available_seats(client, sid)

    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 99999},
    )
    assert resp.status_code == 400
    assert "asientos" in resp.json()["detail"].lower()
    assert _available_seats(client, sid) == antes  # no se altera el aforo


def test_compra_de_todos_los_asientos_y_luego_falla(client, user_headers):
    sid = _showtime_id(client)
    total = _available_seats(client, sid)

    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "Ana", "quantity": total},
        ).status_code
        == 201
    )
    assert _available_seats(client, sid) == 0

    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1},
    )
    assert resp.status_code == 400


def test_compra_en_funcion_inexistente_devuelve_404(client, user_headers):
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": 999999, "customer_name": "Ana", "quantity": 1},
    )
    assert resp.status_code == 404


def test_compra_con_cantidad_invalida(client, user_headers):
    sid = _showtime_id(client)
    for cantidad in (0, -1):
        resp = client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "Ana", "quantity": cantidad},
        )
        assert resp.status_code == 422


def test_usuario_solo_ve_sus_reservas(client, user_headers, admin_headers):
    sid = _showtime_id(client)
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "User", "quantity": 1},
    )
    client.post(
        "/tickets/book",
        headers=admin_headers,
        json={"showtime_id": sid, "customer_name": "Admin", "quantity": 1},
    )

    assert client.get("/tickets", headers=user_headers).json()["total"] == 1
    assert client.get("/tickets", headers=admin_headers).json()["total"] == 2


def test_listado_de_reservas_requiere_autenticacion(client):
    assert client.get("/tickets").status_code == 401


def test_usuario_no_puede_ver_reserva_ajena(client, user_headers, admin_headers):
    sid = _showtime_id(client)
    admin_ticket = client.post(
        "/tickets/book",
        headers=admin_headers,
        json={"showtime_id": sid, "customer_name": "Admin", "quantity": 1},
    ).json()["ticket"]["id"]

    assert client.get(f"/tickets/{admin_ticket}", headers=user_headers).status_code == 403
    assert client.get(f"/tickets/{admin_ticket}", headers=admin_headers).status_code == 200


def test_usuario_puede_ver_su_propia_reserva(client, user_headers):
    sid = _showtime_id(client)
    ticket_id = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1},
    ).json()["ticket"]["id"]

    resp = client.get(f"/tickets/{ticket_id}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket_id


def test_reserva_inexistente_devuelve_404(client, admin_headers):
    assert client.get("/tickets/999999", headers=admin_headers).status_code == 404


def test_paginacion_de_reservas(client, user_headers):
    sid = _showtime_id(client)
    for _ in range(3):
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1},
        )
    body = client.get("/tickets?page=1&size=2", headers=user_headers).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["pages"] == 2


def test_no_se_pueden_vender_mas_asientos_que_el_aforo_en_varias_compras(client, user_headers):
    sid = _showtime_id(client)
    total = _available_seats(client, sid)
    mitad = total // 2

    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "A", "quantity": mitad},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "B", "quantity": mitad},
        ).status_code
        == 201
    )
    # Ya no queda margen (salvo imparidad): cualquier compra extra falla.
    if _available_seats(client, sid) == 0:
        assert (
            client.post(
                "/tickets/book",
                headers=user_headers,
                json={"showtime_id": sid, "customer_name": "C", "quantity": 1},
            ).status_code
            == 400
        )


# --------------------------------------------------------------------------- #
#  Listado para gestión (?scope=all / ?search=) y cancelación de entradas
# --------------------------------------------------------------------------- #
def _book(
    client,
    headers,
    sid: int,
    name: str = "Ana López",
    seats: list[str] | None = None,
    quantity: int = 2,
) -> dict:
    payload = {"showtime_id": sid, "customer_name": name, "quantity": quantity}
    if seats is not None:
        payload["seats"] = seats
    resp = client.post("/tickets/book", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["ticket"]


def _seat_flags(client, sid: int) -> dict[str, bool]:
    mapa = client.get(f"/showtimes/{sid}/seats").json()
    return {
        seat["label"]: seat["reserved"] for row in mapa["rows"] for seat in row["seats"]
    }


def test_scope_all_solo_para_el_personal(client, user_headers, manager_headers, admin_headers):
    sid = _showtime_id(client)
    _book(client, user_headers, sid)

    # Un cliente normal no puede pedir la lista completa.
    assert client.get("/tickets?scope=all", headers=user_headers).status_code == 403

    # El manager ve las suyas por defecto (ninguna) y todas con ?scope=all.
    assert client.get("/tickets", headers=manager_headers).json()["total"] == 0
    todas = client.get("/tickets?scope=all", headers=manager_headers)
    assert todas.status_code == 200
    assert todas.json()["total"] == 1
    assert todas.json()["items"][0]["username"] == "user"

    # El admin (informático) sigue viendo todas también sin parámetro.
    assert client.get("/tickets", headers=admin_headers).json()["total"] == 1
    assert client.get("/tickets?scope=all", headers=admin_headers).json()["total"] == 1

    # El alcance solo admite 'mine' o 'all'.
    assert client.get("/tickets?scope=otra", headers=manager_headers).status_code == 422


def test_scope_mine_filtra_las_propias(client, manager_headers, user_headers):
    sid = _showtime_id(client)
    _book(client, user_headers, sid, quantity=1)
    _book(client, manager_headers, sid, name="Jefe", quantity=1)

    propias = client.get("/tickets?scope=mine", headers=manager_headers).json()
    assert propias["total"] == 1
    assert propias["items"][0]["customer_name"] == "Jefe"


def test_search_encuentra_las_entradas_de_un_jugador(client, manager_headers, user_headers):
    sid = _showtime_id(client)
    _book(client, user_headers, sid, name="Pepe Viaje", quantity=1)

    # Por nombre del cliente...
    por_cliente = client.get("/tickets?scope=all&search=Pepe", headers=manager_headers)
    assert por_cliente.status_code == 200
    assert por_cliente.json()["total"] == 1

    # ...o por nombre de usuario.
    por_usuario = client.get("/tickets?scope=all&search=user", headers=manager_headers)
    assert por_usuario.json()["total"] == 1

    sin_coincidencias = client.get(
        "/tickets?scope=all&search=NoExiste", headers=manager_headers
    )
    assert sin_coincidencias.json()["total"] == 0


def test_reserva_expone_usuario_y_funcion(client, manager_headers, user_headers):
    sid = _showtime_id(client)
    ticket_id = _book(client, user_headers, sid)["id"]

    resp = client.get(f"/tickets/{ticket_id}", headers=manager_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "user"
    assert body["movie_title"]
    assert body["room"]
    assert body["start_time"]


def test_manager_cancela_reserva_y_libera_las_butacas(client, manager_headers, user_headers):
    sid = _showtime_id(client)
    antes = _available_seats(client, sid)
    ticket_id = _book(client, user_headers, sid, seats=["A1", "A2"])["id"]

    assert _available_seats(client, sid) == antes - 2
    assert all(_seat_flags(client, sid)[s] for s in ("A1", "A2"))

    resp = client.delete(f"/tickets/{ticket_id}", headers=manager_headers)
    assert resp.status_code == 204, resp.text

    # Se libera el aforo y las butacas vuelven a estar libres.
    assert _available_seats(client, sid) == antes
    assert not any(_seat_flags(client, sid)[s] for s in ("A1", "A2"))

    # La entrada desaparece de los listados y ya no se puede consultar.
    assert client.get("/tickets", headers=user_headers).json()["total"] == 0
    assert client.get(f"/tickets/{ticket_id}", headers=manager_headers).status_code == 404

    # Y las butacas liberadas admiten una nueva compra.
    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={
                "showtime_id": sid,
                "customer_name": "Otra Persona",
                "seats": ["A1", "A2"],
                "quantity": 2,
            },
        ).status_code
        == 201
    )


def test_admin_tambien_puede_cancelar_reservas(client, admin_headers, user_headers):
    sid = _showtime_id(client)
    antes = _available_seats(client, sid)
    ticket_id = _book(client, user_headers, sid, quantity=1)["id"]

    assert client.delete(f"/tickets/{ticket_id}", headers=admin_headers).status_code == 204
    assert _available_seats(client, sid) == antes
    assert client.get("/tickets", headers=admin_headers).json()["total"] == 0


def test_cancelar_requiere_personal_y_reserva_existente(client, manager_headers, user_headers):
    sid = _showtime_id(client)
    ticket_id = _book(client, user_headers, sid, quantity=1)["id"]

    # Un cliente no puede cancelar (ni siquiera la suya propia) -> 403.
    assert client.delete(f"/tickets/{ticket_id}", headers=user_headers).status_code == 403
    assert client.delete(f"/tickets/{ticket_id}").status_code == 401

    # Reserva inexistente -> 404.
    assert client.delete("/tickets/999999", headers=manager_headers).status_code == 404

    # Sigue intacta: no se ha borrado nada con los intentos fallidos.
    assert client.get("/tickets", headers=user_headers).json()["total"] == 1


def test_cancelada_la_ultima_reserva_se_puede_eliminar_la_funcion(
    client, manager_headers, user_headers
):
    sid = _showtime_id(client)
    ticket_id = _book(client, user_headers, sid, quantity=1)["id"]

    # Mientras haya entradas vendidas la función no se puede borrar (409)...
    assert client.delete(f"/showtimes/{sid}", headers=manager_headers).status_code == 409

    # ...y tras cancelar la reserva, sí.
    assert client.delete(f"/tickets/{ticket_id}", headers=manager_headers).status_code == 204
    assert client.delete(f"/showtimes/{sid}", headers=manager_headers).status_code == 204
