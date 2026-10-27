# Esquemas de salida del panel de la agencia: KPIs por cliente, totales y carga por técnico (spec 010, T07).
from pydantic import BaseModel


class ClientKpi(BaseModel):
    """KPI del mes de un cliente para la consola de la agencia (CA-1, CA-2)."""

    client_id: int
    client_name: str
    service_name: str | None = None
    service_status: str = "operativo"
    # SLA y MTTR calculados desde el Hub (docs/kpi.md, T03 y T06)
    sla_compliance: float | None = None
    mttr: float | None = None
    # Solicitudes del mes (docs/kpi.md, T03)
    open_tickets: int = 0
    closed_tickets: int = 0
    # Horas y costo del mes (docs/kpi.md, T04)
    hours: float = 0.0
    cost: float = 0.0


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
