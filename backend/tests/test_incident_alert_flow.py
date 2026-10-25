# Prueba punta a punta del ciclo de un incidente de alerta: firing → tomar → resolved → cerrar (spec 008, T13).
import json
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.models import AuditLog

FIXTURES = Path(__file__).parent / "fixtures"
TOKEN = "token-de-alertmanager-de-pruebas"


def _alert(anonymous, name: str):
    payload = json.loads((FIXTURES / f"alertmanager_{name}.json").read_text(encoding="utf-8"))
    response = anonymous.post("/api/alerts/alertmanager", json=payload, headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200, response.text
    return response.json()["results"][0]


def _service_status(as_agency, namespace="cliente-restaurante") -> str:
    return {s["namespace"]: s["service_status"] for s in as_agency.get("/api/services/status").json()}[namespace]


def test_ciclo_de_alerta_de_punta_a_punta(anonymous, as_agency, seeded, session_factory, monkeypatch):
    monkeypatch.setattr(settings, "alertmanager_token", TOKEN)

    # 1. La v2 rota tumba el sitio: Alertmanager avisa y se abre el P1
    incident_id = _alert(anonymous, "firing")["incident_id"]
    assert _alert(anonymous, "firing_repetido")["result"] == "duplicado"
    [listed] = as_agency.get("/api/incidents", params={"status": "abierto"}).json()
    assert (listed["id"], listed["priority"], listed["source"]) == (incident_id, "P1", "alerta")
    assert _service_status(as_agency) == "caido"

    # 2. El técnico lo toma; mitigarlo a mano no se permite porque es de alerta
    assert as_agency.post(f"/api/incidents/{incident_id}/acknowledge").status_code == 200
    assert as_agency.post(f"/api/incidents/{incident_id}/mitigate").status_code == 409

    # 3. El sitio vuelve: el resolved lo deja mitigado y el servicio operativo
    assert _alert(anonymous, "resolved")["result"] == "mitigado"
    detail = as_agency.get(f"/api/incidents/{incident_id}").json()
    assert detail["status"] == "mitigado"
    assert detail["mitigated_at"].startswith("2026-10-24T19:04:10")
    assert _service_status(as_agency) == "operativo"

    # 4. Se cierra con la causa raíz
    closed = as_agency.post(f"/api/incidents/{incident_id}/close", json={"root_cause": "La v2 respondía 500 en /health"})
    assert closed.status_code == 200
    assert [e["type"] for e in closed.json()["events"]] == ["detectado", "tomado", "recuperado", "cerrado"]
    assert [e["actor_name"] for e in closed.json()["events"]][0] == "Sistema"

    with session_factory() as db:
        logs = db.scalars(
            select(AuditLog).where(AuditLog.entity == "incident", AuditLog.entity_id == incident_id).order_by(AuditLog.id)
        )
        assert [(log.action, log.user_id is None) for log in logs] == [
            ("crear", True), ("tomar", False), ("mitigar", True), ("cerrar", False),
        ]

    # 5. La misma falla, si vuelve después, abre un incidente nuevo
    assert _alert(anonymous, "firing")["result"] == "creado"
