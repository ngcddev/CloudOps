# Mensaje para el cliente cuando su sitio se recuperó (spec 009, T09). Texto determinista con la plantilla
# de la misión: no es IA, pero se trata como un borrador y la agencia decide si lo envía (principio 6).
from datetime import datetime, timezone

from app.models.incident import Incident
from app.services.incident_flow import IncidentFlowError
from app.services.sla import BOGOTA

# Plantilla de la misión (constitution/mission.md), en el lenguaje del glosario: sin «incidente»,
# «rollback», «P1» ni nada técnico (principio 8)
PLANTILLA = (
    "Detectamos una falla temporal en su sitio a las {hora}. Activamos la recuperación y a las {hora_fin} "
    "el servicio volvió a funcionar. Tiempo total: {duracion}."
)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _duracion(minutos: int) -> str:
    if minutos < 1:
        return "menos de 1 minuto"
    return "1 minuto" if minutos == 1 else f"{minutos} minutos"


def client_message(incident: Incident) -> str:
    """Texto para el cliente con las horas reales de Colombia; falla si el incidente aún no se mitigó.

    Las horas se muestran al minuto y la duración sale de esas mismas horas, para que el mensaje no se
    contradiga (14:00 → 14:07 es «7 minutos» aunque la medición exacta sea 7 min 30 s).
    """
    if incident.mitigated_at is None:
        raise IncidentFlowError("El mensaje al cliente se genera cuando el incidente está mitigado.")
    inicio = _as_utc(incident.started_at).astimezone(BOGOTA).replace(second=0, microsecond=0)
    fin = _as_utc(incident.mitigated_at).astimezone(BOGOTA).replace(second=0, microsecond=0)
    minutos = int((fin - inicio).total_seconds() // 60)
    return PLANTILLA.format(hora=inicio.strftime("%H:%M"), hora_fin=fin.strftime("%H:%M"), duracion=_duracion(minutos))
