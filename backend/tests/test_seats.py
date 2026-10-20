"""Pruebas funcionales de la selección de asientos."""

from app.seats import all_seat_labels


def _showtime_id(client, index: int = 0) -> int:
    return client.get("/showtimes?size=100").json()["items"][index]["id"]


def _showtime(client, showtime_id: int) -> dict:
    return client.get(f"/showtimes/{showtime_id}").json()


def _available_seats(client, showtime_id: int) -> int:
    return _showtime(client, showtime_id)["available_seats"]


def _seat_map(client, showtime_id: int) -> dict:
    return client.get(f"/showtimes/{showtime_id}/seats").json()


def _flat_status(client, showtime_id: int) -> dict[str, bool]:
    mapa = _seat_map(client, showtime_id)
    return {s["label"]: s["reserved"] for row in mapa["rows"] for s in row["seats"]}


def test_mapa_de_asientos_inicial(client):
    sid = _showtime_id(client)
    total = _showtime(client, sid)["total_seats"]

    mapa = _seat_map(client, sid)
    assert mapa["showtime_id"] == sid
    assert mapa["total_seats"] == total
    assert mapa["available_seats"] == total
    assert mapa["reserved"] == []

    etiquetas = [s["label"] for row in mapa["rows"] for s in row["seats"]]
    assert len(etiquetas) == total
    assert etiquetas == all_seat_labels(total)
    assert all(s["reserved"] is False for row in mapa["rows"] for s in row["seats"])


def test_mapa_de_funcion_inexistente_devuelve_404(client):
    assert client.get("/showtimes/999999/seats").status_code == 404


def test_compra_con_asientos_reserva_butacas(client, user_headers):
    sid = _showtime_id(client)
    antes = _available_seats(client, sid)

    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 2, "seats": ["A1", "A2"]},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert sorted(body["ticket"]["seats"]) == ["A1", "A2"]
    assert body["ticket"]["quantity"] == 2
    assert body["remaining_seats"] == antes - 2

    estado = _flat_status(client, sid)
    assert estado["A1"] is True and estado["A2"] is True
    assert estado["A3"] is False
    assert set(_seat_map(client, sid)["reserved"]) == {"A1", "A2"}


def test_butaca_ocupada_no_se_puede_reasignar(client, user_headers, admin_headers):
    sid = _showtime_id(client)
    assert (
        client.post(
            "/tickets/book",
            headers=user_headers,
            json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1, "seats": ["B1"]},
        ).status_code
        == 201
    )

    resp = client.post(
        "/tickets/book",
        headers=admin_headers,
        json={"showtime_id": sid, "customer_name": "Luis", "quantity": 1, "seats": ["B1"]},
    )
    assert resp.status_code == 409
    assert "ocupada" in resp.json()["detail"].lower()


def test_no_se_puede_repetir_butaca_en_una_compra(client, user_headers):
    sid = _showtime_id(client)
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 2, "seats": ["C1", "C1"]},
    )
    assert resp.status_code == 400
    assert "repetir" in resp.json()["detail"].lower() or "misma" in resp.json()["detail"].lower()


def test_butaca_inexistente_devuelve_400(client, user_headers):
    sid = _showtime_id(client)
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 1, "seats": ["Z99"]},
    )
    assert resp.status_code == 400
    assert "existen" in resp.json()["detail"].lower()


def test_numero_de_butacas_debe_coincidir_con_entradas(client, user_headers):
    sid = _showtime_id(client)
    # 2 butacas pero 3 entradas -> error
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 3, "seats": ["D1", "D2"]},
    )
    assert resp.status_code == 400
    assert "coincidir" in resp.json()["detail"].lower()

    # 1 butaca pero 2 entradas -> error
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 2, "seats": ["D1"]},
    )
    assert resp.status_code == 400


def test_asignacion_automatica_reserva_butacas(client, user_headers):
    sid = _showtime_id(client)
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 3},
    )
    assert resp.status_code == 201
    butacas = resp.json()["ticket"]["seats"]
    assert len(butacas) == 3
    assert len(set(butacas)) == 3

    estado = _flat_status(client, sid)
    assert all(estado[b] for b in butacas)
    # Deben ser las primeras libres del plano.
    assert butacas == all_seat_labels(_showtime(client, sid)["total_seats"])[:3]


def test_dos_compras_no_comparten_butaca(client, user_headers, admin_headers):
    sid = _showtime_id(client)
    client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "A", "quantity": 2, "seats": ["E1", "E2"]},
    )
    # El segundo intento con una butaca ya tomada falla por completo (no reserva la libre).
    resp = client.post(
        "/tickets/book",
        headers=admin_headers,
        json={"showtime_id": sid, "customer_name": "B", "quantity": 2, "seats": ["E2", "E3"]},
    )
    assert resp.status_code == 409

    estado = _flat_status(client, sid)
    assert estado["E2"] is True
    assert estado["E3"] is False  # no se reservó parcialmente


def test_total_de_reservas_por_butaca_no_supera_aforo(client, user_headers):
    sid = _showtime_id(client)
    total = _showtime(client, sid)["total_seats"]
    # Reservamos todas las butacas de una fila (10) y comprobamos el descuento exacto.
    fila = all_seat_labels(total)[:10]
    resp = client.post(
        "/tickets/book",
        headers=user_headers,
        json={"showtime_id": sid, "customer_name": "Ana", "quantity": 10, "seats": fila},
    )
    assert resp.status_code == 201
    assert resp.json()["remaining_seats"] == total - 10
