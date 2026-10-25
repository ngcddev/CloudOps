# Comprueba que los payloads guardados de Alertmanager tienen lo que lee el webhook (spec 008, T09).
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("alertmanager_*.json")), ids=lambda p: p.name)
def test_el_payload_tiene_los_campos_del_webhook(path):
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["version"] == "4"
    assert payload["status"] in {"firing", "resolved"}
    assert payload["alerts"]
    for alert in payload["alerts"]:
        assert alert["labels"]["namespace"].startswith("cliente-")
        assert alert["labels"]["priority"] in {"P1", "P2", "P3", "P4"}
        assert {"status", "startsAt", "endsAt", "fingerprint"} <= alert.keys()


def test_hay_firing_repetido_y_resolved_de_la_misma_falla():
    def load(name):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))["alerts"][0]

    firing, repeated, resolved = (
        load("alertmanager_firing.json"),
        load("alertmanager_firing_repetido.json"),
        load("alertmanager_resolved.json"),
    )
    assert firing["fingerprint"] == repeated["fingerprint"] == resolved["fingerprint"]
    assert resolved["status"] == "resolved"
    assert resolved["endsAt"] > resolved["startsAt"]
