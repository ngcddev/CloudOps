# Endpoints de solicitudes: creación, bandeja y detalle (spec 004, T09).
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.client import Client
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.ticket_event import TicketEvent
from app.models.user import User
from app.models.work_log import WorkLog
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
    WorkLogCreate,
    WorkLogOut,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


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


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    """Crea una solicitud asociada a un servicio existente."""
    if db.get(Service, data.service_id) is None:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    if data.created_by_id is not None and db.get(User, data.created_by_id) is None:
        raise HTTPException(status_code=404, detail="El usuario creador no existe.")

    ticket = Ticket(**data.model_dump(), status="abierto")
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
):
    """Lista solicitudes con filtros opcionales por cliente, estado y prioridad."""
    query = select(Ticket).join(Ticket.service).join(Service.project).join(Project.client)
    if client_id is not None:
        query = query.where(Client.id == client_id)
    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)
    if priority is not None:
        query = query.where(Ticket.priority == priority)
    return db.scalars(query.order_by(Ticket.id)).all()


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Devuelve una solicitud con su historial y horas registradas."""
    return _get_ticket_or_404(db, ticket_id)


@router.post("/{ticket_id}/classify", response_model=TicketOut)
def classify_ticket(ticket_id: int, data: TicketClassify, db: Session = Depends(get_db)):
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
            type="prioridad",
            from_value=old_priority,
            to_value=selected_priority,
            note=data.correction_reason,
            internal=False,
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(ticket_id: int, data: TicketAssign, db: Session = Depends(get_db)):
    """Asigna un responsable y registra el cambio en el historial."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if db.get(User, data.assignee_id) is None:
        raise HTTPException(status_code=404, detail="El usuario responsable no existe.")
    if data.actor_id is not None and db.get(User, data.actor_id) is None:
        raise HTTPException(status_code=404, detail="El usuario que asigna no existe.")

    old_assignee = str(ticket.assignee_id) if ticket.assignee_id is not None else None
    ticket.assignee_id = data.assignee_id
    db.add(
        TicketEvent(
            ticket=ticket,
            actor_id=data.actor_id,
            type="asignacion",
            from_value=old_assignee,
            to_value=str(data.assignee_id),
            internal=False,
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/transition", response_model=TicketOut)
def transition_ticket(ticket_id: int, data: TicketTransition, db: Session = Depends(get_db)):
    """Cambia el estado si la transición pertenece al flujo permitido."""
    ticket = _get_ticket_or_404(db, ticket_id)
    if data.actor_id is not None and db.get(User, data.actor_id) is None:
        raise HTTPException(status_code=404, detail="El usuario que cambia el estado no existe.")

    old_status = ticket.status
    try:
        transition(ticket, data.new_status)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    db.add(
        TicketEvent(
            ticket=ticket,
            actor_id=data.actor_id,
            type="estado",
            from_value=old_status,
            to_value=data.new_status,
            internal=False,
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/work-logs", response_model=WorkLogOut, status_code=status.HTTP_201_CREATED)
def create_work_log(ticket_id: int, data: WorkLogCreate, db: Session = Depends(get_db)):
    """Registra horas trabajadas por un usuario en una solicitud."""
    if db.get(Ticket, ticket_id) is None:
        raise HTTPException(status_code=404, detail="La solicitud no existe.")
    if db.get(User, data.user_id) is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")

    work_log = WorkLog(ticket_id=ticket_id, **data.model_dump())
    db.add(work_log)
    db.commit()
    db.refresh(work_log)
    return work_log