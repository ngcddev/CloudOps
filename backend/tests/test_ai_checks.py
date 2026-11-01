# Pruebas de los controles de los textos del asistente (spec 012, T03-T04).
from datetime import datetime, timedelta, timezone

import pytest

from app.models import Incident
from app.services.ai_checks import forbidden_terms
from app.services.messages import client_message

# 14:00 en Colombia
INICIO = datetime(2026, 10, 24, 19, 0, tzinfo=timezone.utc)


# ---------- T03: términos prohibidos ----------


@pytest.mark.parametrize(
    "texto, termino",
    [
        ("Hicimos un ROLLBACK del sitio.", "rollback"),
        ("Fue un incidente p1.", "prioridad P1-P4"),
        ("Reiniciamos el Pod.", "pod"),
        ("Volvimos de la v2 a la v1.", "versión vN"),
        ("Publicamos la v1.1.", "versión vN"),
        ("Argo CD sincronizó.", "argo"),
        ("El clúster respondió.", "clúster"),
        ("Hubo un error 500.", "error 500"),
    ],
)
def test_detecta_la_jerga_sin_importar_mayusculas(texto, termino):
    assert termino in forbidden_terms(texto)


@pytest.mark.parametrize(
    "texto",
    [
        "Podemos ayudarle en lo que necesite.",  # «pod» dentro de otra palabra
        "Su sitio volvió a funcionar de forma estable.",
        "La visita del 21 de octubre quedó registrada.",
    ],
)
def test_no_marca_palabras_comunes(texto):
    assert forbidden_terms(texto) == []


def test_el_mensaje_de_la_009_sale_limpio():
    incident = Incident(
        service_id=1, priority="P1", status="mitigado", source="alerta", title="Sitio caído",
        started_at=INICIO, response_due_at=INICIO, resolution_due_at=INICIO,
        mitigated_at=INICIO + timedelta(minutes=7),
    )
    assert forbidden_terms(client_message(incident)) == []


def test_devuelve_todos_los_terminos_en_orden():
    assert forbidden_terms("El commit en Gitea hizo rollback del pod") == ["rollback", "commit", "gitea", "pod"]
