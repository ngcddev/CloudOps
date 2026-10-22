# Pruebas del flujo de estados de una solicitud de cambio (spec 005, T09).
from datetime import datetime, timezone

import pytest

from app.models.change_request import ChangeRequest
from app.services.change_flow import transition


def make_change(status: str = "pendiente") -> ChangeRequest:
    return ChangeRequest(
        ticket_id=1, service_id=1, from_version="v1", to_version="v1.1", status=status
    )


def test_acepta_el_camino_completo_y_fija_horas_y_usuario():
    change = make_change()
    approved = datetime(2026, 10, 11, 14, 0, tzinfo=timezone.utc)
    deployed = datetime(2026, 10, 11, 14, 2, tzinfo=timezone.utc)

    transition(change, "aprobada", actor_id=7, now=approved)
    transition(change, "en_validacion", actor_id=7, now=approved)
    transition(change, "desplegada", now=deployed)

    assert change.status == "desplegada"
    assert change.approved_by_id == 7
    assert change.approved_at == approved
    assert change.deployed_at == deployed


def test_rechazar_guarda_el_motivo():
    change = make_change()

    transition(change, "rechazada", reason="  La portada no cumple la guía  ")

    assert change.status == "rechazada"
    assert change.rejection_reason == "La portada no cumple la guía"
    assert change.approved_by_id is None


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_rechazar_sin_motivo_falla(reason):
    change = make_change()

    with pytest.raises(ValueError, match="motivo"):
        transition(change, "rechazada", reason=reason)

    assert change.status == "pendiente"


@pytest.mark.parametrize(
    ("current", "new"),
    [
        ("pendiente", "en_validacion"),
        ("pendiente", "desplegada"),
        ("aprobada", "desplegada"),
        ("aprobada", "rechazada"),
        ("en_validacion", "rechazada"),
        ("en_validacion", "aprobada"),
        ("desplegada", "pendiente"),
        ("desplegada", "en_validacion"),
        ("rechazada", "aprobada"),
        ("rechazada", "pendiente"),
    ],
)
def test_rechaza_saltos_invalidos(current, new):
    change = make_change(current)

    with pytest.raises(ValueError, match="No se permite"):
        transition(change, new, reason="x")

    assert change.status == current


def test_un_estado_desconocido_no_tiene_salidas():
    with pytest.raises(ValueError, match="No se permite"):
        transition(make_change("otro"), "aprobada")
