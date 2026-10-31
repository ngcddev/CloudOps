# Pruebas de los KPIs del mes (spec 010, T03): solicitudes abiertas/cerradas y cumplimiento de SLA.
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.integrations.prometheus import Transport
from app.models.client import Client
from app.models.incident import Incident
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


def test_mttr_del_mes_promedia_las_mitigaciones(db):
    service = _servicio(db)
    inicio = datetime(2026, 10, 5, 14, 0, tzinfo=timezone.utc)

    db.add(
        Incident(
            service_id=service.id, priority="P1", status="mitigado", source="alerta", title="Sitio caído",
            started_at=inicio, response_due_at=inicio + timedelta(minutes=15), resolution_due_at=inicio + timedelta(hours=4),
            mitigated_at=inicio + timedelta(minutes=6),
        )
    )
    db.add(
        Incident(
            service_id=service.id, priority="P1", status="cerrado", source="alerta", title="Sitio caído",
            started_at=inicio, response_due_at=inicio + timedelta(minutes=15), resolution_due_at=inicio + timedelta(hours=4),
            mitigated_at=inicio + timedelta(minutes=10), closed_at=inicio + timedelta(minutes=12),
        )
    )
    db.commit()

    # (6 min + 10 min) / 2 = 8 min de MTTR
    assert kpi.mttr_del_mes(db, service.project.client_id, MES) == 8.0


def test_mttr_del_mes_sin_incidentes_da_none(db):
    service = _servicio(db)

    assert kpi.mttr_del_mes(db, service.project.client_id, MES) is None


def _transport_ok(valor: float) -> Transport:
    def transport(url, timeout):
        import json

        return 200, json.dumps({"status": "success", "data": {"result": [{"metric": {}, "value": [1761446400, str(valor)]}]}}).encode()

    return transport


def _transport_error() -> Transport:
    def transport(url, timeout):
        raise OSError("Prometheus caído")

    return transport


def test_disponibilidad_del_mes_con_prometheus_simulado(db):
    service = _servicio(db)
    client_id = service.project.client_id

    # 0.992 de promedio de probe_success = 99,2 % de disponibilidad
    assert kpi.disponibilidad_del_mes(db, client_id, MES, transport=_transport_ok(0.992)) == 99.2
    # El SLO del plan Premium es 99,9: la disponibilidad del mes no cumplió
    assert kpi.cumple_objetivo(db, client_id, MES, transport=_transport_ok(0.992)) is False


def test_disponibilidad_consulta_la_etiqueta_client_del_job_sitios(db):
    """Prometheus etiqueta `client="restaurante"`, no el namespace completo (008, T22)."""
    from urllib.parse import unquote

    service = _servicio(db)
    urls = []

    def transport(url, timeout):
        import json

        urls.append(unquote(url))
        return 200, json.dumps(
            {"status": "success", "data": {"result": [{"metric": {}, "value": [1761446400, "0.992"]}]}}
        ).encode()

    assert kpi.disponibilidad_del_mes(db, service.project.client_id, MES, transport=transport) == 99.2
    assert 'avg_over_time(probe_success{client="restaurante"}' in urls[0]


def test_cumple_objetivo_con_slo_distinto(db):
    service = _servicio(db)
    client_id = service.project.client_id
    plan = db.get(Plan, service.plan_id)
    assert plan is not None
    plan.slo_availability = Decimal("99.0")
    db.commit()

    assert kpi.cumple_objetivo(db, client_id, MES, transport=_transport_ok(0.992)) is True


def test_disponibilidad_con_prometheus_caido_da_none(db):
    service = _servicio(db)

    assert kpi.disponibilidad_del_mes(db, service.project.client_id, "2026-11", transport=_transport_error()) is None
    assert kpi.cumple_objetivo(db, service.project.client_id, "2026-11", transport=_transport_error()) is None
    assert kpi.latencia_p95_del_mes(db, service.project.client_id, "2026-11", transport=_transport_error()) is None


def _transport_rango(valores: list[float]) -> Transport:
    def transport(url, timeout):
        import json
        from datetime import datetime, timezone

        inicio = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
        return 200, json.dumps(
            {
                "status": "success",
                "data": {
                    "result": [
                        {
                            "metric": {},
                            "values": [
                                [inicio + i * 300, str(valor)] for i, valor in enumerate(valores)
                            ],
                        }
                    ],
                },
            }
        ).encode()

    return transport


def test_serie_disponibilidad_devuelve_porcentajes_cada_5_min(db):
    service = _servicio(db)

    puntos = kpi.serie_disponibilidad(
        db, service.project.client_id, MES, transport=_transport_rango([0.99, 0.0, 1.0])
    )

    assert puntos is not None
    assert [valor for _, valor in puntos] == [99.0, 0.0, 100.0]
    assert (puntos[1][0] - puntos[0][0]).total_seconds() == 300


def test_serie_latencia_p95_devuelve_los_puntos(db):
    service = _servicio(db)

    puntos = kpi.serie_latencia_p95(
        db, service.project.client_id, MES, transport=_transport_rango([0.2, 0.45])
    )

    assert puntos is not None
    assert [valor for _, valor in puntos] == [0.2, 0.45]


def test_series_con_prometheus_caido_dan_none(db):
    service = _servicio(db)

    assert kpi.serie_disponibilidad(db, service.project.client_id, MES, transport=_transport_error()) is None
    assert kpi.serie_latencia_p95(db, service.project.client_id, MES, transport=_transport_error()) is None
