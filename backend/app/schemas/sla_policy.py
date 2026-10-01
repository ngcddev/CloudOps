# Esquema de salida de las políticas de SLA: tiempos por prioridad (plan 001#api).
from pydantic import BaseModel, ConfigDict


class SlaPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    priority: str
    response_minutes: int
    resolution_minutes: int
    clock: str
