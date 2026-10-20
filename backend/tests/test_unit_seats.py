"""Pruebas unitarias del plano de asientos (app/seats.py)."""

from app.seats import (
    SEATS_PER_ROW,
    all_seat_labels,
    is_valid_seat,
    normalize_seat,
    row_label,
    seat_layout,
)


def test_row_label_secuencia():
    assert row_label(0) == "A"
    assert row_label(1) == "B"
    assert row_label(25) == "Z"
    assert row_label(26) == "AA"
    assert row_label(27) == "AB"


def test_layout_reparte_en_filas_de_diez():
    layout = seat_layout(25)
    assert [label for label, _ in layout] == ["A", "B", "C"]
    assert len(layout[0][1]) == SEATS_PER_ROW
    assert layout[2][1] == ["C1", "C2", "C3", "C4", "C5"]


def test_layout_suma_el_aforo_total():
    for total in (1, 9, 10, 11, 80, 120, 127):
        etiquetas = all_seat_labels(total)
        assert len(etiquetas) == total
        assert len(set(etiquetas)) == total  # sin duplicados


def test_is_valid_seat_y_normalizacion():
    assert is_valid_seat(80, "A1")
    assert is_valid_seat(80, "H10")
    assert is_valid_seat(80, " a1 ")  # normaliza espacios y mayúsculas
    assert not is_valid_seat(80, "I1")  # la sala de 80 tiene filas A-H
    assert not is_valid_seat(80, "A0")
    assert not is_valid_seat(80, "A11")  # solo 10 butacas por fila
    assert normalize_seat(" b3 ") == "B3"
