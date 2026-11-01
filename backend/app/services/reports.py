# Datos de los reportes mensuales (spec 013): el operativo de la agencia y el ejecutivo de cada cliente.
# Los KPI salen de services/kpi.py, las mismas funciones del dashboard (spec 010), para que coincidan (CA-5).
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from app.services import kpi


def previous_month(month: str) -> str:
    """Mes anterior a `YYYY-MM` (enero → diciembre del año anterior)."""
    year, number = (int(part) for part in month.split("-"))
    return f"{year - 1}-12" if number == 1 else f"{year}-{number - 1:02d}"


def _average(values: list[float | None]) -> float | None:
    """Promedio de los clientes con dato; None si ninguno tiene (nunca un 0 inventado)."""
    present = [value for value in values if value is not None]
    return round(sum(present) / len(present), 2) if present else None


def _totals(rows: list[dict]) -> dict:
    """Total de la agencia: suma lo que se cuenta y promedia lo que es porcentaje o tiempo."""
    return {
        "open_tickets": sum(row["open_tickets"] for row in rows),
        "closed_tickets": sum(row["closed_tickets"] for row in rows),
        "hours": round(sum(row["hours"] for row in rows), 2),
        "cost": round(sum(row["cost"] for row in rows), 2),
        "availability": _average([row["availability"] for row in rows]),
        "sla_compliance": _average([row["sla_compliance"] for row in rows]),
        "mttr": _average([row["mttr"] for row in rows]),
    }


def _technicians(db: Session, month: str) -> list[dict]:
    """Carga de cada técnico de la agencia en el mes, igual que el panel."""
    return [
        {
            "user_id": user.id,
            "name": user.name,
            "hours": kpi.horas_del_tecnico(db, user.id, month),
            "load": kpi.carga_tecnico(db, user.id, month),
        }
        for user in db.scalars(select(User).where(User.role == "agencia").order_by(User.id)).all()
    ]


def operational(db: Session, month: str) -> dict:
    """Reporte operativo del mes: KPI de cada cliente y de la agencia, con el mes anterior al lado (CA-1)."""
    before = previous_month(month)
    clients = db.scalars(
        select(Client).options(selectinload(Client.projects).selectinload(Project.services)).order_by(Client.id)
    ).all()
    rows = []
    for client in clients:
        current = kpi.client_month_kpis(db, client, month)
        previous = kpi.client_month_kpis(db, client, before)
        rows.append(
            {
                "client_id": client.id,
                "client_name": client.name,
                "service_name": current["service_name"],
                "current": current,
                "previous": previous,
            }
        )
    params = kpi.kpi_params()
    return {
        "kind": "operativo",
        "month": month,
        "previous_month": before,
        "currency": params["currency"],
        "hourly_cost": params["hourly_cost"],
        "clients": rows,
        "totals": {
            "current": _totals([row["current"] for row in rows]),
            "previous": _totals([row["previous"] for row in rows]),
        },
        "technicians": _technicians(db, month),
    }
