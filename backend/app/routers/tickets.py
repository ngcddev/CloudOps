# Endpoints de solicitudes: creación, bandeja y detalle (spec 004, T09).
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.client import Client
from app.models.project import Project
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketDetail, TicketOut

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