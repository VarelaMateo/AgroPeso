from datetime import date

from config.database import SessionLocal
from models.ticket_model import EstadoTicket, Ticket, TicketDB
from repository.ticket_repository import TicketRepository

with SessionLocal() as session:
    repo = TicketRepository(session)

    # Ticket abierto: sin peso bruto
    t = repo.create_ticket(Ticket(date.today(), "Prueba Abierto", None, 15000, None, 1))
    assert t.estado == EstadoTicket.ABIERTO and t.peso_neto is None

    abiertos = [x.id for x in repo.get_all_tickets(EstadoTicket.ABIERTO)]
    assert t.id in abiertos

    # Cerrarlo
    t.peso_bruto = 45000
    t.estado = EstadoTicket.CERRADO
    cerrado = repo.update_ticket(t)
    assert cerrado.peso_neto == 30000

    assert t.id in [x.id for x in repo.get_all_tickets(EstadoTicket.CERRADO)]
    assert t.id not in [x.id for x in repo.get_all_tickets(EstadoTicket.ABIERTO)]

    # Limpieza: borra la fila de prueba
    session.delete(session.get(TicketDB, t.id))
    session.commit()

    print("OK")