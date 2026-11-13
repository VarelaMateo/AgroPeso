from typing import Optional

from repository.ticket_repository import TicketRepository
from models.ticket_model import EstadoTicket, Ticket
from models.user_model import Rol
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

    def obtener_ticket_de_usuario(self, ticket_id: int, user) -> Ticket:
        ticket = self.obtener_ticket(ticket_id)
        if user.rol == Rol.CLIENTE and ticket.supplier_id != user.supplier_id:
            raise TicketNoEncontradoError(f"No existe el ticket von id {ticket_id}")
        return ticket
    
    def obtener_todos_los_tickets (self, user, estado: Optional[EstadoTicket] = None) -> list[Ticket]:
        if user.rol == Rol.CLIENTE:
            if user.supplier_id is None:
                return[] #Un cliente sin proveedor no debe nada
            return self.repository.get_all_tickets(estado = estado, supplier_id = user.supplier_id)
        return self.repository.get_all_tickets(estado = estado)

    def validar_pesos (self, peso_tara: int, peso_bruto: int) -> None:
        if peso_tara >= peso_bruto:
            raise ReglaNegocioError(f"El peso bruto ({peso_bruto}) debe ser mayor a la tara ({peso_tara})")
           