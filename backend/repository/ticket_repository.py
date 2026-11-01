from typing import Optional
from sqlalchemy.orm import Session
from models.ticket_model import Ticket, TicketDB

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

    def _to_db (self, ticket: Ticket) -> TicketDB:
        return TicketDB(
            fecha = ticket.fecha,
            chofer = ticket.chofer,
            patente=ticket.patente,
            peso_tara=ticket.peso_tara,
            peso_bruto=ticket.peso_bruto,
            peso_neto=ticket.peso_neto,   # la tabla lo exige
            supplier_id=ticket.supplier_id,
            product_id=ticket.product_id,
            transporte=ticket.transporte,
            numero_ticket=ticket.numero_ticket,
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
        )
