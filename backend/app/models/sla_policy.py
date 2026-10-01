# Modelo de política de SLA: tiempos por prioridad P1–P4 (tabla sla_policies, plan 001 / spec 000).
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SlaPolicy(Base):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    priority: Mapped[str] = mapped_column(String(2), unique=True)
    response_minutes: Mapped[int] = mapped_column(Integer)
    resolution_minutes: Mapped[int] = mapped_column(Integer)
    # "24x7" o "horario_plan" (el reloj corre solo en el horario de atención del plan)
    clock: Mapped[str] = mapped_column(String(30))
