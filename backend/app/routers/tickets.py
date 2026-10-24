# Endpoints de solicitudes: creación, bandeja y detalle (spec 004, T09), con sesión y alcance por cliente (spec 007).
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import client_scope, current_user, require_agency
from app.models.client import Client
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.ticket_event import TicketEvent
from app.models.user import User
from app.models.work_log import WorkLog
from app.services import audit
from app.services.priority import classify
from app.services.sla import due_dates
from app.services.ticket_flow import transition
from app.schemas.ticket import (
    TicketAssign,
    TicketClassify,
    TicketCreate,
    TicketDetail,
    TicketOut,
    TicketTransition,
    TicketEventOut,
    WorkLogCreate,
    WorkLogOut,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
CLIENT_STATUS_LABELS = {
    "abierto": "Abierto",
    "en_progreso": "En progreso",
    "en_espera": "En espera",
    "resuelto": "Resuelto",
    "cerrado": "Cerrado",
}
# Estados de una solicitud de cambio tal como los ve el cliente (docs/glosario.md)
CLIENT_CHANGE_LABELS = {
    "pendiente": "Pendiente",
    "aprobada": "Aprobada",
    "en_validacion": "En validación",
    "desplegada": "Publicada",
    "rechazada": "Rechazada",
    "fallida": "No se pudo publicar",
}


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    query = (
        select(Ticket)
        .options(selectinload(Ticket.events), selectinload(Ticket.work_logs))
        .where(Ticket.id == ticket_id)
    )
    ticket = db.scalar(query)
    if ticket is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe.")
    return ticket


def _check_client_access(ticket: Ticket, user: User) -> None:
    """Un cliente solo ve sus solicitudes; las de otro responden igual que si no existieran."""
    scope = client_scope(user)
    if scope is not None and ticket.service.project.client_id != scope:
        raise HTTPException(status_code=404, detail="La solicitud no existe.")


def _present_ticket(ticket: Ticket, user: User, detail: bool = False, check_scope: bool = True):
    # La lista ya filtra por cliente en SQL: repetir la comprobación fila por fila sumaría consultas
    if check_scope:
        _check_client_access(ticket, user)
    result = TicketDetail.model_validate(ticket) if detail else TicketOut.model_validate(ticket)
    if user.role == "cliente":
        result.status = CLIENT_STATUS_LABELS.get(result.status, result.status)
        if detail:
            result.events = [event for event in result.events if not event.internal]
            for event in result.events:
                if event.type == "cambio":
                    event.from_value = CLIENT_CHANGE_LABELS.get(event.from_value, event.from_value)
                    event.to_value = CLIENT_CHANGE_LABELS.get(event.to_value, event.to_value)
    return result


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Crea una solicitud a nombre del usuario de la sesión; un cliente solo puede hacerlo sobre sus servicios."""
    service = db.get(Service, data.service_id)
    scope = client_scope(user)
    if service is None or (scope is not None and service.project.client_id != scope):
        raise HTTPException(status_code=404, detail="El servicio no existe.")

    ticket = Ticket(**data.model_dump(), created_by_id=user.id, status="abierto")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    client_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Lista solicitudes con filtros opcionales por estado y prioridad.

    La agencia puede filtrar por cliente; un cliente siempre ve solo las suyas.
    """
    query = select(Ticket).join(Ticket.service).join(Service.project).join(Project.client)
    scope = client_scope(user)
    if scope is not None:
        query = query.where(Client.id == scope)
    elif client_id is not None:
        query = query.where(Client.id == client_id)
    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    tickets = db.scalars(query.order_by(Ticket.id)).all()
    return [_present_ticket(ticket, user, check_scope=False) for ticket in tickets]


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Devuelve una solicitud con su historial y horas registradas."""
    return _present_ticket(_get_ticket_or_404(db, ticket_id), user, detail=True)


@router.post("/{ticket_id}/classify", response_model=TicketOut)
def classify_ticket(
    ticket_id: int,
    data: TicketClassify,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Clasifica una solicitud, calcula su SLA y registra la decisión."""
    ticket = _get_ticket_or_404(db, ticket_id)
    proposed_priority = classify(data.impact, data.urgency)
    selected_priority = data.priority or proposed_priority
    if selected_priority != proposed_priority and not data.correction_reason:
        raise HTTPException(
            status_code=422,
            detail="Debe indicar un motivo para corregir la prioridad propuesta.",
        )

    if ticket.created_at is None:
        raise HTTPException(status_code=422, detail="La solicitud no tiene fecha de creación.")
    service = db.get(Service, ticket.service_id)
    if service is None or service.plan is None:
        raise HTTPException(status_code=422, detail="El servicio no tiene un plan asignado.")

    created_at = ticket.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    response_due_at, resolution_due_at = due_dates(created_at, selected_priority, service.plan)
    old_priority = ticket.priority
    ticket.impact = data.impact
    ticket.urgency = data.urgency
    ticket.priority = selected_priority
    ticket.response_due_at = response_due_at
    ticket.resolution_due_at = resolution_due_at
    db.add(
        TicketEvent(
            ticket=ticket,
            actor_id=actor.id,
            type="prioridad",
            from_value=old_priority,
            to_value=selected_priority,
            note=data.correction_reason,
            internal=False,
        )
    )
    audit.record(
        db, actor, "cambiar_prioridad", "ticket", ticket.id,
        {"de": old_priority, "a": selected_priority, "motivo": data.correction_reason},
        audit.request_ip(request),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    data: TicketAssign,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Asigna un responsable y registra el cambio en el historial."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if db.get(User, data.assignee_id) is None:
        raise HTTPException(status_code=404, detail="El usuario responsable no existe.")

    old_assignee = str(ticket.assignee_id) if ticket.assignee_id is not None else None
    ticket.assignee_id = data.assignee_id
    db.add(
        TicketEvent(
            ticket=ticket,
            actor_id=actor.id,
            type="asignacion",
            from_value=old_assignee,
            to_value=str(data.assignee_id),
            internal=False,
        )
    )
    audit.record(
        db, actor, "asignar", "ticket", ticket.id,
        {"de": old_assignee, "a": str(data.assignee_id)}, audit.request_ip(request),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/transition", response_model=TicketOut)
def transition_ticket(
    ticket_id: int,
    data: TicketTransition,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_agency),
):
    """Cambia el estado si la transición pertenece al flujo permitido."""
    ticket = _get_ticket_or_404(db, ticket_id)

    old_status = ticket.status
    try:
        transition(ticket, data.new_status)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    db.add(
        TicketEvent(
            ticket=ticket,
            actor_id=actor.id,
            type="estado",
            from_value=old_status,
            to_value=data.new_status,
            internal=False,
        )
    )
    audit.record(
        db, actor, "cambiar_estado", "ticket", ticket.id,
        {"de": old_status, "a": data.new_status}, audit.request_ip(request),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/work-logs", response_model=WorkLogOut, status_code=status.HTTP_201_CREATED)
def create_work_log(
    ticket_id: int,
    data: WorkLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_agency),
):
    """Registra las horas trabajadas por el usuario de la sesión en una solicitud."""
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe.")

    work_log = WorkLog(ticket_id=ticket_id, user_id=user.id, **data.model_dump())
    db.add(work_log)
    audit.record(
        db, user, "registrar_horas", "ticket", ticket_id,
        {"horas": float(data.hours)}, audit.request_ip(request),
    )
    db.commit()
    db.refresh(work_log)
    return work_log