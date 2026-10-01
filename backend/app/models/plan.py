# Modelo de plan contratado por un servicio (tabla plans, spec 001).
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    slo_availability: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    support_hours: Mapped[str] = mapped_column(String(100))
    cpu_quota: Mapped[str] = mapped_column(String(50))
    memory_quota: Mapped[str] = mapped_column(String(50))
    monthly_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    included_hours: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
