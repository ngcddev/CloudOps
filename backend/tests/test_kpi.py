# Pruebas de los KPIs del mes (spec 010, T03): solicitudes abiertas/cerradas y cumplimiento de SLA.
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.client import Client
from app.models.plan import Plan
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.user import User
from app.models.work_log import WorkLog
from app.services import kpi


MES = "2026-10"


def _servicio(db) -> Service:
    """Un cliente con un proyecto, un servicio y su plan, para las solicitudes de prueba."""
    client = Client(name="Restaurante La Sazón")
    db.add(client)
    db.commit()
    db.refresh(client)
    plan = Plan(code="premium", name="Premium", slo_availability=99.9, support_hours="24x7", cpu_quota="1000m", memory_quota="1Gi")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    project = Project(client_id=client.id, name="Sitio web La Sazón")
    db.add(project)
    db.commit()
    db.refresh(project)
    service = Service(
        project_id=project.id, plan_id=plan.id, name="Sitio web", host="restaurante.hub.local",
        template="landing", namespace="cliente-restaurante",
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def _solicitud(
    db,
    service_id: int,
    status: str,
    created_at: datetime,
    resolved_at: datetime | None = None,
    response_due_at: datetime | None = None,
    resolution_due_at: datetime | None = None,
    first_response_at: datetime | None = None,
    closed_at: datetime | None = None,
) -> Ticket:
    ticket = Ticket(
        service_id=service_id,
        created_by_id=None,
        assignee_id=None,
        title="Solicitud",
        description="Descripción",
        impact="alto",
        urgency="alta",
        priority="P2",
        status=status,
        response_due_at=response_due_at,
        resolution_due_at=resolution_due_at,
        first_response_at=first_response_at,
        resolved_at=resolved_at,
        closed_at=closed_at,
        created_at=created_at,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def test_cumplimiento_sla_con_4_cerrados_dentro_y_1_fuera_da_80(db):
    service = _servicio(db)
    created_at = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    response_due_at = created_at + timedelta(minutes=15)
    resolution_due_at = created_at + timedelta(hours=4)

    for _ in range(4):
        _solicitud(
            db, service.id, "cerrado", created_at, response_due_at=response_due_at,
            resolution_due_at=resolution_due_at, first_response_at=created_at + timedelta(minutes=5),
            resolved_at=created_at + timedelta(minutes=10), closed_at=created_at + timedelta(minutes=12),
        )
    _solicitud(
        db, service.id, "cerrado", created_at, response_due_at=response_due_at, resolution_due_at=resolution_due_at,
        first_response_at=created_at + timedelta(minutes=5), resolved_at=created_at + timedelta(hours=6),
        closed_at=created_at + timedelta(hours=6, minutes=10),
    )

    assert kpi.cumplimiento_sla(db, service.project.client_id, MES) == 80.0


def test_cumplimiento_sla_con_ninguna_solicitud_terminada_da_none(db):
    service = _servicio(db)
    _solicitud(db, service.id, "abierto", datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc))

    assert kpi.cumplimiento_sla(db, service.project.client_id, MES) is None


def test_solicitudes_del_mes_cuentan_abiertas_y_cerradas(db):
    service = _servicio(db)
    created_at = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    response_due_at = created_at + timedelta(minutes=15)
    resolution_due_at = created_at + timedelta(hours=4)

    abierto = _solicitud(db, service.id, "abierto", created_at, response_due_at=response_due_at, resolution_due_at=resolution_due_at)
    _solicitud(
        db, service.id, "cerrado", created_at, response_due_at=response_due_at, resolution_due_at=resolution_due_at,
        first_response_at=created_at + timedelta(minutes=5), resolved_at=created_at + timedelta(minutes=10),
        closed_at=created_at + timedelta(minutes=12),
    )
    _solicitud(
        db, service.id, "resuelto", datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc), response_due_at=response_due_at,
        resolution_due_at=resolution_due_at, first_response_at=created_at, resolved_at=created_at,
    )

    assert kpi.solicitudes_abiertas(db, service.project.client_id, MES) == 1
    assert kpi.solicitudes_cerradas(db, service.project.client_id, MES) == 1


def test_costo_del_cliente_suma_horas_por_hora_del_parametro(db):
    service = _servicio(db)
    created_at = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    response_due_at = created_at + timedelta(minutes=15)
    resolution_due_at = created_at + timedelta(hours=4)

    ticket = _solicitud(
        db, service.id, "cerrado", created_at, response_due_at=response_due_at, resolution_due_at=resolution_due_at,
        first_response_at=created_at + timedelta(minutes=5), resolved_at=created_at + timedelta(minutes=10),
        closed_at=created_at + timedelta(minutes=12),
    )
    tecnico = User(name="Sofía Ramírez", email="sofia@forjadigital.test", role="agencia")
    db.add(tecnico)
    db.commit()
    db.refresh(tecnico)
    for hours, note in ((Decimal("3"), "Revisión del menú"), (Decimal("2"), "Ajuste de render")):
        db.add(WorkLog(ticket_id=ticket.id, user_id=tecnico.id, hours=hours, note=note))
    db.commit()

    # 3 horas + 2 horas a 25 000 por hora = 125 000 de costo para el cliente
    assert kpi.horas_por_cliente(db, service.project.client_id, MES) == 5.0
    assert kpi.costo_por_cliente(db, service.project.client_id, MES) == 125000.0


def test_carga_del_tecnico_con_30_horas_registradas_y_120_disponibles_da_25(db):
    service = _servicio(db)
    created_at = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)
    response_due_at = created_at + timedelta(minutes=15)
    resolution_due_at = created_at + timedelta(hours=4)
    ticket = _solicitud(
        db, service.id, "cerrado", created_at, response_due_at=response_due_at, resolution_due_at=resolution_due_at,
        first_response_at=created_at + timedelta(minutes=5), resolved_at=created_at + timedelta(minutes=10),
        closed_at=created_at + timedelta(minutes=12),
    )
    tecnico = User(name="Sofía Ramírez", email="sofia@forjadigital.test", role="agencia")
    db.add(tecnico)
    db.commit()
    db.refresh(tecnico)
    db.add(WorkLog(ticket_id=ticket.id, user_id=tecnico.id, hours=Decimal("10"), note="Revisión"))
    db.add(WorkLog(ticket_id=ticket.id, user_id=tecnico.id, hours=Decimal("20"), note="Ajuste de render"))
    db.commit()

    # 30 h registradas con 120 disponibles del mes = 25 % de carga
    assert kpi.horas_del_tecnico(db, tecnico.id, MES) == 30.0
    assert kpi.carga_tecnico(db, tecnico.id, MES) == 0.25
