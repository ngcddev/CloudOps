# Pruebas del flujo de estados de una solicitud (spec 004, T05).
from datetime import datetime, timezone

import pytest

from app.models.ticket import Ticket
from app.services.ticket_flow import transition


def make_ticket(status: str = "abierto") -> Ticket:
    return Ticket(service_id=1, title="Solicitud", description="Descripción", status=status)


def test_acepta_el_ciclo_valido_completo_y_fija_fechas():
    ticket = make_ticket()
    first_response = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)
    resolved = datetime(2026, 10, 4, 15, 30, tzinfo=timezone.utc)
    closed = datetime(2026, 10, 4, 15, 45, tzinfo=timezone.utc)

    transition(ticket, "en_progreso", first_response)
    transition(ticket, "en_espera", first_response)
    transition(ticket, "en_progreso", resolved)
    transition(ticket, "resuelto", resolved)
    transition(ticket, "cerrado", closed)

    assert ticket.status == "cerrado"
    assert ticket.first_response_at == first_response
    assert ticket.resolved_at == resolved
    assert ticket.closed_at == closed


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        ("abierto", "resuelto"),
        ("abierto", "cerrado"),
        ("en_progreso", "cerrado"),
        ("resuelto", "en_progreso"),
        ("cerrado", "abierto"),
    ],
)
def test_rechaza_saltos_invalidos(current_status, new_status):
    ticket = make_ticket(current_status)

    with pytest.raises(ValueError, match="No se permite"):
        transition(ticket, new_status)


def test_fija_first_response_al_pasar_a_en_progreso():
    ticket = make_ticket()
    first_response = datetime(2026, 10, 4, 14, 0, tzinfo=timezone.utc)

    transition(ticket, "en_progreso", first_response)

    assert ticket.first_response_at == first_response