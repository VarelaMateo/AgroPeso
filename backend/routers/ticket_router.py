from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.ticket_model import Ticket, EstadoTicket
from repository.ticket_repository import TicketRepository
from schemas.ticket_schema import TicketCreate, TicketResponse, TicketClose
from services.ticket_service import TicketService
from utils.exceptions import ReglaNegocioError, TicketNoEncontradoError

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/", response_model=TicketResponse, status_code=201)
def create_ticket(datos: TicketCreate, db: Session = Depends(get_db)):
    repository = TicketRepository(db)
    service = TicketService(repository)
    ticket = Ticket(**datos.model_dump()) # esquema -> entidad pura
    #datos.model_dump() lo convierte en un diccionario, y Ticket(**...) lo desarma como argumentos con nombre para crear la entidad.
    
    try:
        return service.registrar_pesada(ticket)
    except ReglaNegocioError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[TicketResponse])
def listar_ticket(estado: Optional[EstadoTicket] = None, db: Session = Depends(get_db)):
    repository= TicketRepository(db)
    service = TicketService(repository)
    return service.obtener_todos_los_tickets(estado)

@router.get("/{ticket_id}", response_model=TicketResponse)
def obtener_ticket(ticket_id: int, db: Session = Depends(get_db)):
    repository= TicketRepository(db)
    service = TicketService(repository)

    try:
        return service.obtener_ticket(ticket_id)
    except TicketNoEncontradoError as e:
        raise HTTPException(status_code = 404, detail = str(e))

@router.patch("/{ticket_id}/cerrar", response_model = TicketResponse)
def cerrar_ticket(ticket_id: int, datos: TicketClose, db: Session=Depends(get_db)):
    repository= TicketRepository(db)
    service = TicketService(repository)

    try:
        return service.cerrar_ticket(ticket_id, datos.peso_bruto)
    except TicketNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ReglaNegocioError as e:
        raise HTTPException(status_code=400, detail=str(e))
