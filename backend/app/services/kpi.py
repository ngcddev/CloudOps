# KPIs del mes para el panel de la agencia y el portal del cliente (spec 010, T03-T11).
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations import prometheus
from app.integrations.prometheus import Transport
from app.models.client import Client
from app.models.incident import Incident
from app.models.plan import Plan
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.work_log import WorkLog
from app.services.sla import BOGOTA

# Carpeta donde el seed escribe los JSON de datos (misma convención que backend/app/seed.py).
SEED_DIR = Path(os.getenv("SEED_DIR") or Path(__file__).resolve().parents[2] / "seed")

# Valores de trabajo mientras la spec 000 no cierra los precios y la capacidad (docs/kpi.md, T01).
KPI_DEFAULTS = {
    "hourly_cost": 25000,
    "technician_monthly_hours": 120,
    "currency": "COP",
    "at_risk_ratio": 0.8,
}


def kpi_params() -> dict:
    """Lee los parámetros de KPI de `seed/kpi_params.json`; si no existe usa los de trabajo."""
    try:
        data = json.loads((SEED_DIR / "kpi_params.json").read_text(encoding="utf-8"))
        return {**KPI_DEFAULTS, **data}
    except (OSError, ValueError):
        return dict(KPI_DEFAULTS)

# Estados con solución: la solicitud respondió y resolvió (o cerró) su caso; ya no sigue abierta.
ESTADOS_TERMINADOS = {"resuelto", "cerrado"}


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite devuelve las fechas sin zona; se guardan siempre en UTC, así que se les pone."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def month_bounds(month: str) -> tuple[datetime, datetime]:
    """Rango [inicio, fin) del mes `YYYY-MM` en America/Bogota, convertido a UTC para la base de datos.

    El mes arranca a las 00:00 hora de Colombia (06:00 UTC) y termina el primer día del mes siguiente.
    """
    anio, mes = (int(part) for part in month.split("-"))
    inicio_local = datetime(anio, mes, 1, tzinfo=BOGOTA)
    if mes == 12:
        fin_local = datetime(anio + 1, 1, 1, tzinfo=BOGOTA)
    else:
        fin_local = datetime(anio, mes + 1, 1, tzinfo=BOGOTA)
    inicio = _as_utc(inicio_local)
    fin = _as_utc(fin_local)
    assert inicio is not None and fin is not None
    return inicio, fin


def tickets_del_cliente(db: Session, client_id: int, month: str) -> list[Ticket]:
    """Solicitudes del cliente creado en el mes, del más viejo al más reciente."""
    inicio, fin = month_bounds(month)
    return list(
        db.scalars(
            select(Ticket)
            .join(Ticket.service)
            .join(Service.project)
            .join(Project.client)
            .where(Client.id == client_id, Ticket.created_at >= inicio, Ticket.created_at < fin)
            .order_by(Ticket.created_at, Ticket.id)
        ).all()
    )


def solicitudes_abiertas(db: Session, client_id: int, month: str | None = None) -> int:
    """Solicitudes del mes que siguen abiertas (no cerraron su caso)."""
    tickets = tickets_del_cliente(db, client_id, month or mes_actual())
    return sum(1 for ticket in tickets if ticket.status not in ESTADOS_TERMINADOS)


def solicitudes_cerradas(db: Session, client_id: int, month: str | None = None) -> int:
    """Solicitudes del mes que cerraron su caso (tuvieron solución registrada)."""
    tickets = tickets_del_cliente(db, client_id, month or mes_actual())
    return sum(1 for ticket in tickets if ticket.status in ESTADOS_TERMINADOS)


def horas_por_cliente(db: Session, client_id: int, month: str | None = None) -> float:
    """Horas registradas (Σ `work_logs.hours`) de las solicitudes del cliente en el mes."""
    tickets = tickets_del_cliente(db, client_id, month or mes_actual())
    total = 0.0
    for ticket in tickets:
        for work_log in ticket.work_logs:
            total += float(work_log.hours)
    return total


def costo_por_cliente(db: Session, client_id: int, month: str | None = None) -> float:
    """Costo del mes del cliente: horas registradas × `hourly_cost` (docs/kpi.md, T01)."""
    return horas_por_cliente(db, client_id, month) * float(kpi_params()["hourly_cost"])


def _servicio_de_cliente(db: Session, client_id: int) -> Service | None:
    """Servicio principal del cliente, para armar las consultas de Prometheus con su namespace."""
    return db.scalar(
        select(Service)
        .join(Service.project)
        .join(Project.client)
        .where(Client.id == client_id)
        .order_by(Service.id)
    )


def nombre_cliente(namespace: str | None) -> str:
    """Etiqueta `client` de Prometheus: el namespace sin el prefijo `cliente-` (008, T22).

    El job `sitios` fija `client` a partir del namespace (`cliente-restaurante` → `restaurante`);
    consultar con el namespace completo devolvía vacío y la pantalla mostraba «sin datos».
    """
    return (namespace or "").removeprefix("cliente-")


def _ventana_del_mes(month: str) -> tuple[int, int] | None:
    """Duración y `offset` en segundos del mes, para `avg_over_time` sobre el rango correcto.

    Devuelve `None` si el mes todavía no empezó (no hay nada que promediar).
    """
    inicio, fin = month_bounds(month)
    ahora = datetime.now(timezone.utc)
    fin_real = min(fin, ahora)
    if fin_real <= inicio:
        return None
    segundos = max(int((fin_real - inicio).total_seconds()), 1)
    offset = max(int((ahora - fin_real).total_seconds()), 0)
    return segundos, offset


def disponibilidad_del_mes(
    db: Session, client_id: int, month: str | None = None, transport: Transport | None = None
) -> float | None:
    """Disponibilidad del mes del cliente: `avg_over_time(probe_success{client="<c>"}[<mes>]) × 100`.

    El rango se calcula desde el inicio del mes hasta ahora (o hasta el fin del mes si ya pasó) y se
    desplaza con `offset` cuando el mes es anterior. Con Prometheus caído o sin serie devuelve `None`
    («sin datos»): nunca un 100 % inventado (CA-8).
    """
    service = _servicio_de_cliente(db, client_id)
    if service is None:
        return None
    mes = month or mes_actual()
    ventana = _ventana_del_mes(mes)
    if ventana is None:
        return None
    segundos, offset = ventana
    promql = f'avg_over_time(probe_success{{client="{nombre_cliente(service.namespace)}"}}[{segundos}s]'
    if offset:
        promql += f" offset {offset}s"
    promql += ")"
    valor = prometheus.query(promql, mes, transport=transport)
    if valor is None:
        return None
    return round(valor * 100, 2)


def objetivo_disponibilidad(db: Session, client_id: int) -> float | None:
    """SLO de disponibilidad del plan del cliente; `None` si el cliente no tiene plan."""
    return db.scalar(
        select(Plan.slo_availability)
        .join(Service.plan)
        .join(Service.project)
        .join(Project.client)
        .where(Client.id == client_id)
    )


def cumple_objetivo(
    db: Session, client_id: int, month: str | None = None, transport: Transport | None = None
) -> bool | None:
    """La disponibilidad del mes cumplió el SLO del plan del cliente? `None` si no hay datos."""
    disponibilidad = disponibilidad_del_mes(db, client_id, month, transport=transport)
    if disponibilidad is None:
        return None
    slo = objetivo_disponibilidad(db, client_id)
    if slo is None:
        return None
    return disponibilidad >= float(slo)


def latencia_p95_del_mes(
    db: Session, client_id: int, month: str | None = None, transport: Transport | None = None
) -> float | None:
    """Latencia p95 del mes con las métricas de Traefik que expone la spec 008."""
    service = _servicio_de_cliente(db, client_id)
    if service is None:
        return None
    promql = (
        "histogram_quantile(0.95, sum by (le) (rate("
        f'traefik_service_request_duration_seconds_bucket{{service=~"{service.namespace}-.*"}}[5m])))'
    )
    return prometheus.query(promql, month or mes_actual(), transport=transport)


# Paso de las series de las gráficas: un punto cada 5 min (spec 010, T11 y plan.md).
SERIES_STEP_SECONDS = 300


def serie_disponibilidad(
    db: Session, client_id: int, month: str | None = None, transport: Transport | None = None
) -> list[tuple[datetime, float]] | None:
    """Puntos de disponibilidad del sitio del cliente cada 5 min, en porcentaje (100 = arriba).

    `None` si Prometheus falla; lista vacía si no hay serie (CA-8).
    """
    service = _servicio_de_cliente(db, client_id)
    if service is None:
        return None
    inicio, fin = month_bounds(month or mes_actual())
    puntos = prometheus.query_range(
        f'probe_success{{client="{nombre_cliente(service.namespace)}"}}',
        inicio,
        fin,
        step_seconds=SERIES_STEP_SECONDS,
        transport=transport,
    )
    if puntos is None:
        return None
    return [(marca, round(valor * 100, 2)) for marca, valor in puntos]


def serie_latencia_p95(
    db: Session, client_id: int, month: str | None = None, transport: Transport | None = None
) -> list[tuple[datetime, float]] | None:
    """Puntos de latencia p95 del mes cada 5 min, en segundos; `None` si Prometheus falla."""
    service = _servicio_de_cliente(db, client_id)
    if service is None:
        return None
    inicio, fin = month_bounds(month or mes_actual())
    promql = (
        "histogram_quantile(0.95, sum by (le) (rate("
        f'traefik_service_request_duration_seconds_bucket{{service=~"{service.namespace}-.*"}}[5m])))'
    )
    return prometheus.query_range(
        promql, inicio, fin, step_seconds=SERIES_STEP_SECONDS, transport=transport
    )


def horas_del_tecnico(db: Session, user_id: int, month: str | None = None) -> float:
    """Horas registradas por un técnico en el mes: Σ `work_logs.hours` de sus tickets creados en el mes."""
    inicio, fin = month_bounds(month or mes_actual())
    total = db.scalar(
        select(func.sum(WorkLog.hours))
        .join(Ticket, WorkLog.ticket_id == Ticket.id)
        .where(WorkLog.user_id == user_id, Ticket.created_at >= inicio, Ticket.created_at < fin)
    )
    return float(total or 0)


def carga_tecnico(db: Session, user_id: int, month: str | None = None) -> float:
    """Carga del técnico del mes: horas registradas ÷ horas disponibles del mes (`technician_monthly_hours`)."""
    return horas_del_tecnico(db, user_id, month) / float(kpi_params()["technician_monthly_hours"])


def mttr_del_mes(db: Session, client_id: int, month: str | None = None) -> float | None:
    """MTTR del mes: promedio (solución − inicio) en minutos de los incidentes mitigados/cerrados.

    Sin incidentes mitigados en el mes devuelve `None` (CA-9): no se reporta un MTTR de 0 inventado.
    """
    inicio, fin = month_bounds(month or mes_actual())
    incidents = db.scalars(
        select(Incident)
        .join(Incident.service)
        .join(Service.project)
        .join(Project.client)
        .where(
            Client.id == client_id,
            Incident.started_at >= inicio,
            Incident.started_at < fin,
            Incident.status.in_(["mitigado", "cerrado"]),
        )
    ).all()
    if not incidents:
        return None
    minutos = []
    for incident in incidents:
        solucion = _as_utc(incident.mitigated_at) or _as_utc(incident.closed_at)
        inicio_at = _as_utc(incident.started_at)
        if solucion is None or inicio_at is None:
            continue
        minutos.append((solucion - inicio_at).total_seconds() / 60)
    if not minutos:
        return None
    return round(sum(minutos) / len(minutos), 2)


def cumplimiento_sla(db: Session, client_id: int, month: str | None = None) -> float | None:
    """Porcentaje de las solicitudes cerradas dentro de su plazo de solución: (dentro / terminados) × 100.

    Con ninguna solicitud terminada en el mes devuelve `None` («sin datos»): no se reporta un 100 % inventado.
    """
    tickets = tickets_del_cliente(db, client_id, month or mes_actual())
    terminados = [
        ticket
        for ticket in tickets
        if ticket.status in ESTADOS_TERMINADOS and (ticket.resolved_at is not None or ticket.closed_at is not None)
    ]
    if not terminados:
        return None
    dentro = sum(
        1
        for ticket in terminados
        if (solucion := _as_utc(ticket.resolved_at or ticket.closed_at)) is not None
        and ticket.resolution_due_at is not None
        and solucion <= _as_utc(ticket.resolution_due_at)
    )
    return round((dentro / len(terminados)) * 100, 2)


def mes_actual() -> str:
    """Mes actual en America/Bogota, con el formato `YYYY-MM` que reciben las consultas."""
    return datetime.now(BOGOTA).strftime("%Y-%m")


def client_month_kpis(db: Session, client: Client, month: str) -> dict:
    """Todos los KPI del mes de un cliente para la agencia, en un solo lugar.

    Lo usan el panel de la agencia (spec 010) y el reporte operativo (spec 013): así los números de los dos
    coinciden siempre (CA-5 de la 013).
    """
    service = client.main_service
    return {
        "client_id": client.id,
        "client_name": client.name,
        "service_name": service.name if service is not None else None,
        "service_status": service.status if service is not None else "operativo",
        "availability": disponibilidad_del_mes(db, client.id, month),
        "cumple_objetivo": cumple_objetivo(db, client.id, month),
        "latency_p95": latencia_p95_del_mes(db, client.id, month),
        "sla_compliance": cumplimiento_sla(db, client.id, month),
        "mttr": mttr_del_mes(db, client.id, month),
        "open_tickets": solicitudes_abiertas(db, client.id, month),
        "closed_tickets": solicitudes_cerradas(db, client.id, month),
        "hours": horas_por_cliente(db, client.id, month),
        "cost": costo_por_cliente(db, client.id, month),
    }
