# Carga los datos semilla de seed/*.json (agencia, planes, SLA y clientes) si la base está vacía.
import json
import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agency, Client, Plan, Project, Service, SlaPolicy, User

# En el contenedor la carpeta se indica con SEED_DIR; en tu máquina se usa seed/ del repositorio.
SEED_DIR = Path(os.getenv("SEED_DIR") or Path(__file__).resolve().parents[2] / "seed")


def _read(name: str):
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def _decimal(value) -> Decimal | None:
    """Convierte un número del JSON a Decimal; null significa "por definir"."""
    return None if value is None else Decimal(str(value))


def seed_if_empty(db: Session) -> bool:
    """Carga la semilla solo si no hay agencia. Devuelve True si cargó datos."""
    if db.scalar(select(Agency.id).limit(1)) is not None:
        return False

    clients_data = _read("clients.json")
    agency = Agency(name=clients_data["agency"]["name"])
    db.add(agency)

    plans: dict[str, Plan] = {}
    for item in _read("plans.json"):
        plan = Plan(
            code=item["code"],
            name=item["name"],
            slo_availability=_decimal(item["slo_availability"]),
            support_hours=item["support_hours"],
            cpu_quota=item["cpu_quota"],
            memory_quota=item["memory_quota"],
            monthly_price=_decimal(item["monthly_price"]),
            included_hours=_decimal(item["included_hours"]),
        )
        plans[plan.code] = plan
        db.add(plan)

    for item in _read("sla_policies.json"):
        db.add(SlaPolicy(**item))

    clients_by_name: dict[str, Client] = {}
    for item in clients_data["clients"]:
        client = Client(
            agency=agency,
            name=item["name"],
            contact_name=item["contact_name"],
            email=item["email"],
            phone=item["phone"],
        )
        db.add(client)
        clients_by_name[client.name] = client
        for project_item in item["projects"]:
            project = Project(
                client=client, name=project_item["name"], description=project_item["description"]
            )
            db.add(project)
            for service_item in project_item["services"]:
                plan_code = service_item["plan_code"]
                if plan_code not in plans:
                    raise ValueError(f"El plan «{plan_code}» de seed/clients.json no existe en plans.json.")
                service = Service(
                    project=project,
                    plan=plans[plan_code],
                    name=service_item["name"],
                    host=service_item["host"],
                    template=service_item["template"],
                    namespace=service_item["namespace"],
                )
                db.add(service)

    for item in _read("users.json")["users"]:
        client = None
        if item["role"] == "cliente":
            client_name = item.get("client_name")
            client = clients_by_name.get(client_name)
            if client is None:
                raise ValueError(f"El cliente «{client_name}» del usuario no existe.")
        db.add(
            User(
                name=item["name"],
                email=item["email"],
                role=item["role"],
                client=client,
            )
        )
    db.commit()
    return True
