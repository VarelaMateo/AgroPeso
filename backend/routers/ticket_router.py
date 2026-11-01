from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from models.ticket_model import Ticket
from repository.ticket_repository import TicketRepository
from schemas.ticket_schema import TicketCreate, TicketResponse
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

@router.get("/{ticket_id}", response_model=TicketResponse)
def obtener_ticket(ticket_id: int, db: Session = Depends(get_db)):
    repository= TicketRepository(db)
    service = TicketService(repository)

    try:
        return service.obtener_ticket(ticket_id)
    except TicketNoEncontradoError as e:
        raise HTTPException(status_code = 404, detail = str(e))
