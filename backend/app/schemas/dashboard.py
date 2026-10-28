# Esquemas de salida del panel de la agencia y del portal: KPIs, carga y series (spec 010, T07-T11).
from datetime import datetime

from pydantic import BaseModel


class ClientKpi(BaseModel):
    """KPI del mes de un cliente para la consola de la agencia (CA-1, CA-2)."""

    client_id: int
    client_name: str
    service_name: str | None = None
    service_status: str = "operativo"
    # Disponibilidad del mes y SLO del plan (spec 010, T10); null con Prometheus caído o sin serie
    availability: float | None = None
    cumple_objetivo: bool | None = None
    latency_p95: float | None = None
    # SLA y MTTR calculados desde el Hub (docs/kpi.md, T03 y T06)
    sla_compliance: float | None = None
    mttr: float | None = None
    # Solicitudes del mes (docs/kpi.md, T03)
    open_tickets: int = 0
    closed_tickets: int = 0
    # Horas y costo del mes (docs/kpi.md, T04)
    hours: float = 0.0
    cost: float = 0.0


class ClientDashboardKpi(BaseModel):
    """KPI del mes del cliente para el portal: sin costo, horas ni nombres de técnicos (CA-7)."""

    client_id: int
    client_name: str
    service_name: str | None = None
    service_status: str = "operativo"
    # Disponibilidad y SLO del plan (spec 010, T10); null con Prometheus caído o sin serie
    availability: float | None = None
    cumple_objetivo: bool | None = None
    slo_availability: float | None = None
    latency_p95: float | None = None
    sla_compliance: float | None = None
    mttr: float | None = None
    open_tickets: int = 0
    closed_tickets: int = 0


class ClientIncident(BaseModel):
    """Una falla del mes en el portal: sin técnicos, SLA ni causa interna (CA-4, CA-7)."""

    id: int
    title: str
    status: str
    started_at: datetime


class TechnicianLoad(BaseModel):
    """Carga de un técnico del mes: horas registradas ÷ horas disponibles (CA-2, T05)."""

    user_id: int
    name: str
    hours: float = 0.0
    load: float = 0.0


class AgencyDashboard(BaseModel):
    """Panel de la agencia: KPI por cliente del mes, totales y carga por técnico."""

    month: str
    clients: list[ClientKpi] = []
    technicians: list[TechnicianLoad] = []


class SeriesPoint(BaseModel):
    """Un punto de una gráfica: instante en UTC y valor (porcentaje o segundos)."""

    timestamp: datetime
    value: float


class ClientSeries(BaseModel):
    """Series del mes de un cliente para las gráficas del detalle técnico (CA-6, T11)."""

    client_id: int
    month: str
    slo_availability: float | None = None
    availability: list[SeriesPoint] = []
    latency_p95: list[SeriesPoint] = []
