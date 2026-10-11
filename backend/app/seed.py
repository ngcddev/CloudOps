# Carga los datos semilla de seed/*.json (agencia, planes, SLA y clientes) si la base está vacía.
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agency, Client, Plan, Project, Service, SlaPolicy, Ticket, User
from app.services.sla import due_dates

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

    user_by_email = {user.email: user.id for user in db.scalars(select(User)).all()}
    services_by_host = {service.host: service for service in db.scalars(select(Service)).all()}
    now = datetime.now(timezone.utc)

    seeded_tickets = [
        {
            "service": services_by_host["restaurante.hub.local"],
            "created_by_id": user_by_email["contacto@lasazon.test"],
            "assignee_id": user_by_email["sofia@forjadigital.test"],
            "title": "Necesito actualizar el horario del menú",
            "description": "La página no refleja los nuevos horarios de atención del restaurante.",
            "impact": "alto",
            "urgency": "media",
            "priority": "P2",
            "status": "abierto",
            "created_at": now - timedelta(hours=3),
        },
        {
            "service": services_by_host["ferreteria.hub.local"],
            "created_by_id": user_by_email["contacto@eltornillo.test"],
            "assignee_id": user_by_email["sofia@forjadigital.test"],
            "title": "Los productos destacados no cargan",
            "description": "La sección destacada de productos queda en blanco en la home.",
            "impact": "alto",
            "urgency": "alta",
            "priority": "P1",
            "status": "en_progreso",
            "created_at": now - timedelta(hours=1),
            "first_response_at": now - timedelta(minutes=20),
        },
        {
            "service": services_by_host["consultorio.hub.local"],
            "created_by_id": user_by_email["contacto@dentalpopayan.test"],
            "assignee_id": user_by_email["sofia@forjadigital.test"],
            "title": "Solicito agregar credencial de WhatsApp",
            "description": "Quiero mostrar un botón para contactar por WhatsApp desde la landing.",
            "impact": "medio",
            "urgency": "alta",
            "priority": "P3",
            "status": "resuelto",
            "created_at": now - timedelta(days=2),
            "first_response_at": now - timedelta(days=2, hours=2),
            "resolved_at": now - timedelta(days=1, hours=3),
        },
    ]

    for item in seeded_tickets:
        created_at = item["created_at"]
        service = item["service"]
        response_due_at, resolution_due_at = due_dates(created_at, item["priority"], service.plan)
        ticket = Ticket(
            service_id=service.id,
            created_by_id=item["created_by_id"],
            assignee_id=item["assignee_id"],
            title=item["title"],
            description=item["description"],
            impact=item["impact"],
            urgency=item["urgency"],
            priority=item["priority"],
            status=item["status"],
            response_due_at=response_due_at,
            resolution_due_at=resolution_due_at,
            first_response_at=item.get("first_response_at"),
            resolved_at=item.get("resolved_at"),
            created_at=created_at,
        )
        db.add(ticket)

    db.commit()
    return True
