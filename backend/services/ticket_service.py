from typing import Optional

from repository.ticket_repository import TicketRepository
from models.ticket_model import EstadoTicket, Ticket
from utils.exceptions import ReglaNegocioError, TicketNoEncontradoError 


class TicketService:
    def __init__(self, repository: TicketRepository):
        self.repository = repository

    def registrar_pesada(self, ticket: Ticket) -> Ticket:
        if (ticket.peso_bruto is None):
            ticket.estado = EstadoTicket.ABIERTO
        else:
            self.validar_pesos(ticket.peso_tara, ticket.peso_bruto)
            ticket.estado = EstadoTicket.CERRADO
        return self.repository.create_ticket(ticket)

    def cerrar_ticket(self, ticket_id: int, peso_bruto: int) -> Ticket:
        ticket = self.obtener_ticket(ticket_id)
        
        if ticket.estado == EstadoTicket.CERRADO:
            raise ReglaNegocioError(f"El ticket {ticket_id} ya esta cerrado")
        
        self.validar_pesos(ticket.peso_tara, peso_bruto)

        ticket.peso_bruto = peso_bruto
        ticket.estado = EstadoTicket.CERRADO

        actualizado = self.repository.update_ticket(ticket)
        if actualizado is None:
            raise TicketNoEncontradoError(f"No existe el ticket con id {ticket_id}")
        return actualizado

    def obtener_ticket (self, ticket_id: int) -> Ticket:
        ticket_encontrado = self.repository.get_ticket_by_id(ticket_id) 
        if(ticket_encontrado is None):
            raise TicketNoEncontradoError(f"No existe el ticket con id {ticket_id}")     
        return ticket_encontrado

    def obtener_todos_tickets (self, estado: Optional[EstadoTicket] = None) -> list[Ticket]:
        return self.repository.get_all_tickets(estado)

    def validar_pesos (self, peso_tara: int, peso_bruto: int) -> None:
        if peso_tara >= peso_bruto:
            raise ReglaNegocioError(f"El peso bruto ({peso_bruto}) debe ser mayor a la tara ({peso_tara})")
           