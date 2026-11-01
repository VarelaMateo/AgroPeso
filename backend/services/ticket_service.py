from repository.ticket_repository import TicketRepository
from models.ticket_model import Ticket
from utils.exceptions import ReglaNegocioError, TicketNoEncontradoError 

class TicketService:
    def __init__(self, repository: TicketRepository):
        self.repository = repository

    def registrar_pesada(self, ticket: Ticket) -> Ticket:
        if (ticket.peso_tara >= ticket.peso_bruto):
            raise ReglaNegocioError(f"El peso bruto ({ticket.peso_bruto}) debe ser mayor a la tara ({ticket.peso_tara})")
        return self.repository.create_ticket(ticket)

    def obtener_ticket (self, ticket_id: int) -> Ticket:
        ticket_encontrado = self.repository.get_ticket_by_id(ticket_id) 
        if(ticket_encontrado is None):
            raise TicketNoEncontradoError(f"No existe el ticket con id {ticket_id}")     
        return ticket_encontrado
           