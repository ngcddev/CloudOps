# Pruebas de los datos semilla: que seed/*.json se carguen completos y solo una vez (spec 001, T05).
import json
import shutil

import pytest
from sqlalchemy import func, select

from app import seed
from app.models import Agency, Client, Plan, Project, Service, SlaPolicy, Ticket


def _count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_seed_loads_agency_plans_sla_and_three_clients(seeded):
    assert seeded.scalar(select(Agency.name)) == "Forja Digital"
    assert _count(seeded, Plan) == 3
    assert _count(seeded, SlaPolicy) == 4
    assert _count(seeded, Client) == 3
    assert _count(seeded, Project) == 3
    assert _count(seeded, Service) == 3


def test_seed_adds_three_sample_tickets_in_different_states_and_priorities(seeded):
    tickets = seeded.scalars(select(Ticket).order_by(Ticket.id)).all()
    assert len(tickets) == 3
    statuses = {ticket.status for ticket in tickets}
    priorities = {ticket.priority for ticket in tickets}
    assert statuses == {"abierto", "en_progreso", "resuelto"}
    assert priorities == {"P1", "P2", "P3"}
    assert all("El menú del domingo no aparece" not in ticket.title for ticket in tickets)


def test_seed_uses_the_canonical_names(seeded):
    services = {
        service.host: (service.namespace, service.template, service.plan.code)
        for service in seeded.scalars(select(Service))
    }

    assert services == {
        "restaurante.hub.local": ("cliente-restaurante", "landing", "premium"),
        "ferreteria.hub.local": ("cliente-ferreteria", "landing", "estandar"),
        "consultorio.hub.local": ("cliente-consultorio", "landing_form", "basico"),
    }


def test_seed_does_not_load_twice(seeded):
    assert seed.seed_if_empty(seeded) is False
    assert _count(seeded, Client) == 3


def test_seed_does_not_overwrite_an_existing_database(db):
    db.add(Agency(name="Otra agencia"))
    db.commit()

    assert seed.seed_if_empty(db) is False
    assert _count(db, Plan) == 0


def test_seed_rejects_a_service_with_an_unknown_plan(db, tmp_path, monkeypatch):
    shutil.copytree(seed.SEED_DIR, tmp_path / "seed")
    clients_file = tmp_path / "seed" / "clients.json"
    data = json.loads(clients_file.read_text(encoding="utf-8"))
    data["clients"][0]["projects"][0]["services"][0]["plan_code"] = "inexistente"
    clients_file.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(seed, "SEED_DIR", tmp_path / "seed")

    with pytest.raises(ValueError, match="inexistente"):
        seed.seed_if_empty(db)
