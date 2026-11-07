from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.ticket_model import EstadoTicket, Ticket, TicketDB

class TicketRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_ticket(self, ticket:Ticket) -> Ticket:
        ticket_db = self._to_db(ticket) #Convertis el ticket al objeto de la base de datos
        self.session.add(ticket_db)
        self.session.commit()
        self.session.refresh(ticket_db)
        return self._to_entity(ticket_db) #Devolves el ticket de forma entidad Pura

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        ticket_db = self.session.get(TicketDB, ticket_id)
        if ticket_db is None:
            return None
        return self._to_entity(ticket_db)

    def get_all_tickets(self, estado: Optional[EstadoTicket] = None) -> list[Ticket]:
        consulta = select(TicketDB).order_by(TicketDB.fecha.desc(), TicketDB.id.desc())
        if estado is not None:
            consulta = consulta.where(TicketDB.estado == estado.value)
        ticket_db = self.session.scalars(consulta).all()
        return [self._to_entity(t) for t in ticket_db]

    def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        ticket_db = self.session.get(TicketDB, ticket.id)
        if ticket_db is None:
            return None
        ticket_db.fecha = ticket.fecha
        ticket_db.chofer = ticket.chofer
        ticket_db.patente = ticket.patente
        ticket_db.transporte = ticket.transporte
        ticket_db.supplier_id = ticket.supplier_id
        ticket_db.product_id = ticket.product_id
        ticket_db.peso_tara = ticket.peso_tara
        ticket_db.peso_bruto = ticket.peso_bruto
        ticket_db.peso_neto = ticket.peso_neto
        ticket_db.numero_ticket = ticket.numero_ticket
        ticket_db.estado = ticket.estado.value

        self.session.commit()
        self.session.refresh(ticket_db)
        return self._to_entity(ticket_db)

    def _to_db (self, ticket: Ticket) -> TicketDB:
        return TicketDB(
            fecha = ticket.fecha,
            chofer = ticket.chofer,
            patente=ticket.patente,
            peso_tara=ticket.peso_tara,
            peso_bruto=ticket.peso_bruto,
            peso_neto=ticket.peso_neto,   # None mientras el ticket está abierto
            supplier_id=ticket.supplier_id,
            product_id=ticket.product_id,
            transporte=ticket.transporte,
            numero_ticket=ticket.numero_ticket,
            estado=ticket.estado.value
        )

    def _to_entity (self, ticket_db: TicketDB) -> Ticket: #Recibis el ticket desde la bd y lo convertis a la entidad Pura
        return Ticket(
            id = ticket_db.id,
            fecha = ticket_db.fecha,
            chofer = ticket_db.chofer,
            patente = ticket_db.patente,
            peso_tara = ticket_db.peso_tara,
            peso_bruto = ticket_db.peso_bruto,
            supplier_id = ticket_db.supplier_id,
            product_id = ticket_db.product_id,
            transporte = ticket_db.transporte,
            numero_ticket = ticket_db.numero_ticket,
            estado = EstadoTicket(ticket_db.estado)
        )
