# Esquemas de cliente: lo que entra en POST/PATCH y lo que sale en lista y detalle (plan 001#api).
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ClientSummary(ClientOut):
    """Fila de la lista. main_service queda en null hasta que existan servicios (T07)."""

    main_service: None = None


class ClientDetail(ClientOut):
    """Detalle del cliente. Proyectos y SLA se llenan con T04/T07."""

    projects: list = []
    sla_policies: list = []
