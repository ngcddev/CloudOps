# Esquemas de cliente: lo que entra en POST/PATCH y lo que sale en lista y detalle (plan 001#api).
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.sla_policy import SlaPolicyOut


def _limpiar(value: str | None) -> str | None:
    """Quita espacios; un texto vacío cuenta como dato ausente."""
    if value is None:
        return None
    return value.strip() or None


class ClientBase(BaseModel):
    contact_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("contact_name", "email", "phone")
    @classmethod
    def _opcionales(cls, value: str | None) -> str | None:
        return _limpiar(value)


class ClientCreate(ClientBase):
    name: str = Field(max_length=200)

    @field_validator("name")
    @classmethod
    def _nombre_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre del cliente es obligatorio.")
        return value


class ClientUpdate(ClientBase):
    """Edición parcial: solo se cambian los campos enviados."""

    name: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def _nombre_no_vacio(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        return value.strip()


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    slo_availability: float
    support_hours: str
    cpu_quota: str
    memory_quota: str
    monthly_price: float | None
    included_hours: float | None


class ServiceCreate(BaseModel):
    name: str = Field(max_length=200)
    host: str = Field(max_length=255)
    # Plantillas de sitio de la spec 002; mismos valores que seed/ y el frontend.
    template: Literal["landing", "landing_form"]
    namespace: str = Field(max_length=100)
    plan_id: int | None = Field(default=None, validate_default=True)

    @field_validator("name", "host", "namespace")
    @classmethod
    def _texto_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo es obligatorio.")
        return value

    @field_validator("plan_id")
    @classmethod
    def _plan_obligatorio(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("El servicio necesita un plan.")
        return value


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    template: str
    namespace: str
    status: str
    plan: PlanOut


class ProjectCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def _proyecto_obligatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre del proyecto es obligatorio.")
        return value


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    services: list[ServiceOut] = []


class MainServiceOut(BaseModel):
    """Servicio principal de un cliente, con su plan, para la fila de la lista."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    status: str
    plan: PlanOut


class ClientSummary(ClientOut):
    """Fila de la lista: el cliente con su servicio principal (null si aún no tiene)."""

    main_service: MainServiceOut | None = None


class ClientDetail(ClientOut):
    """Detalle del cliente con sus proyectos, servicios y SLA."""

    projects: list[ProjectOut] = []
    sla_policies: list[SlaPolicyOut] = []
