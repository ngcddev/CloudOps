# Contexto cerrado que recibe el asistente de un incidente (spec 012, T02): solo hechos del Hub.
# Nunca lleva correos, teléfonos ni nombres de técnicos: así ningún dato personal sale del Hub (CA-6),
# y como el asistente solo ve esto, no tiene de dónde inventar horas ni causas (CA-2).
from datetime import datetime, timezone

from app.models.incident import Incident
from app.services.sla import BOGOTA


def _local(value: datetime | None) -> datetime | None:
    """Hora de Colombia al minuto; las fechas sin zona (SQLite) se tratan como UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BOGOTA).replace(second=0, microsecond=0)


def _hhmm(value: datetime | None) -> str | None:
    return value.strftime("%H:%M") if value is not None else None


def incident_facts(incident: Incident) -> dict:
    """Hechos del incidente con las horas de Colombia, listos para armar las instrucciones del asistente.

    La duración sale de las horas mostradas al minuto, igual que el mensaje de la spec 009, para que el
    resumen y el mensaje no se contradigan. `times` son todas las horas que el texto puede citar (T04).
    """
    service = incident.service
    started = _local(incident.started_at)
    ended = _local(incident.mitigated_at)
    duration = int((ended - started).total_seconds() // 60) if ended is not None else None
    moments = (
        incident.started_at,
        incident.acknowledged_at,
        incident.mitigated_at,
        incident.closed_at,
        incident.rollback_at,
        incident.rollback_confirmed_at,
    )
    times = sorted({_hhmm(_local(moment)) for moment in moments if moment is not None})
    if incident.rollback_to_version is not None:
        recovery = "rollback"
    elif ended is not None:
        recovery = "manual"
    else:
        recovery = None
    return {
        "client": service.project.client.name,
        "service": service.name,
        "priority": incident.priority,
        "title": incident.title,
        "status": incident.status,
        "date": started.strftime("%Y-%m-%d"),
        "start_time": _hhmm(started),
        "end_time": _hhmm(ended),
        "duration_minutes": duration,
        "recovery": recovery,
        "from_version": incident.rollback_from_version,
        "to_version": incident.rollback_to_version,
        "root_cause": incident.root_cause,
        "times": times,
    }


def manual_summary(facts: dict) -> str:
    """Resumen técnico armado solo con los hechos, para escribir a mano cuando el asistente no responde (CA-5).

    Es para la agencia: puede nombrar la prioridad, el rollback y las versiones.
    """
    minutes = facts["duration_minutes"]
    duration = "menos de 1 minuto" if minutes < 1 else "1 minuto" if minutes == 1 else f"{minutes} minutos"
    if facts["recovery"] == "rollback":
        action = f"Se hizo rollback de {facts['from_version']} a {facts['to_version']}."
    else:
        action = "Se mitigó a mano."
    text = (
        f"Incidente {facts['priority']} en {facts['service']} ({facts['client']}): {facts['title']}. "
        f"Empezó a las {facts['start_time']} y se recuperó a las {facts['end_time']} ({duration}). {action}"
    )
    if facts["root_cause"]:
        text += f" Causa raíz: {facts['root_cause']}"
    return text
