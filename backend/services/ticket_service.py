from typing import Optional

from repository.product_repository import ProductRepository
from repository.supplier_repository import SupplierRepository
from repository.ticket_repository import TicketRepository
from models.ticket_model import EstadoTicket, Ticket
from models.user_model import Rol
from utils.exceptions import ReferenciaNoEncontradaError, ReglaNegocioError, TicketNoEncontradoError


class TicketService:
    def __init__(self, repository: TicketRepository, supplier_repository: SupplierRepository,
                 product_repository: ProductRepository):
        self.repository = repository
        self.supplier_repository = supplier_repository
        self.product_repository = product_repository

    def registrar_pesada(self, ticket: Ticket) -> Ticket:
        self.validar_proveedor(ticket.supplier_id)
        self.validar_producto(ticket.product_id)
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

    def editar_ticket(self, ticket_id: int, chofer: str, patente: Optional[str], peso_tara: int,
                      peso_bruto: Optional[int], supplier_id: int, product_id: Optional[int]) -> Ticket:
        ticket = self.obtener_ticket(ticket_id)

        if self.supplier_repository.get_supplier_by_id(supplier_id) is None:
            raise ReferenciaNoEncontradaError(f"No existe el proveedor con id {supplier_id}")
        if product_id is not None and self.product_repository.get_product_by_id(product_id) is None:
            raise ReferenciaNoEncontradaError(f"No existe el producto con id {product_id}")

        if peso_bruto is None:
            # Un ticket cerrado no se puede reabrir quitándole el bruto
            if ticket.estado == EstadoTicket.CERRADO:
                raise ReglaNegocioError(f"El ticket {ticket_id} esta cerrado: el peso bruto es obligatorio")
            estado = EstadoTicket.ABIERTO
        else:
            # Cerrado, o abierto al que se le carga el bruto: se valida y queda cerrado
            self.validar_pesos(peso_tara, peso_bruto)
            estado = EstadoTicket.CERRADO

        ticket.chofer = chofer
        ticket.patente = patente
        ticket.peso_tara = peso_tara
        ticket.peso_bruto = peso_bruto  # el neto se recalcula solo (bruto - tara)
        ticket.supplier_id = supplier_id
        ticket.product_id = product_id
        ticket.estado = estado

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
            raise TicketNoEncontradoError(f"No existe el ticket con id {ticket_id}")
        return ticket
    
    def obtener_todos_los_tickets (self, user, estado: Optional[EstadoTicket] = None) -> list[Ticket]:
        if user.rol == Rol.CLIENTE:
            if user.supplier_id is None:
                return[] #Un cliente sin proveedor no debe nada
            return self.repository.get_all_tickets(estado = estado, supplier_id = user.supplier_id)
        return self.repository.get_all_tickets(estado = estado)

    def validar_proveedor(self, supplier_id: int) -> None:
        if self.supplier_repository.get_supplier_by_id(supplier_id) is None:
            raise ReglaNegocioError(f"No existe el proveedor con id {supplier_id}")

    def validar_producto(self, product_id: Optional[int]) -> None:
        # El producto es opcional: solo se valida si viene
        if product_id is not None and self.product_repository.get_product_by_id(product_id) is None:
            raise ReglaNegocioError(f"No existe el producto con id {product_id}")

    def validar_pesos (self, peso_tara: int, peso_bruto: int) -> None:
        if peso_tara >= peso_bruto:
            raise ReglaNegocioError(f"El peso bruto ({peso_bruto}) debe ser mayor a la tara ({peso_tara})")
           