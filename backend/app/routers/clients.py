# Endpoints de clientes: crear, listar, ver y editar (spec 001, T06).
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientDetail, ClientOut, ClientSummary, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clientes"])


def _get_or_404(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="El cliente no existe.")
    return client


@router.get("", response_model=list[ClientSummary])
def list_clients(db: Session = Depends(get_db)):
    """Lista los clientes, del más antiguo al más reciente."""
    return db.scalars(select(Client).order_by(Client.id)).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    """Crea un cliente; solo el nombre es obligatorio."""
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Detalle de un cliente."""
    return _get_or_404(db, client_id)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)):
    """Edita solo los campos enviados."""
    client = _get_or_404(db, client_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client
