from datetime import date

from models.ticket_model import EstadoTicket, Ticket
from repository.ticket_repository import TicketRepository


def crear_ticket(proveedor, bruto=None, estado=EstadoTicket.ABIERTO):
    return Ticket(date.today(), "Ivan Derio", "HKN279", 15160, bruto, proveedor.id,
                  estado=estado)


def test_crear_y_leer_ticket_abierto(session, proveedor):
    repo = TicketRepository(session)
    nuevo = repo.create_ticket(crear_ticket(proveedor))

    assert nuevo.id is not None
    assert nuevo.estado == EstadoTicket.ABIERTO
    assert nuevo.peso_neto is None
    assert repo.get_ticket_by_id(nuevo.id) == nuevo


def test_crear_ticket_cerrado_calcula_el_neto(session, proveedor):
    repo = TicketRepository(session)
    nuevo = repo.create_ticket(crear_ticket(proveedor, 48260, EstadoTicket.CERRADO))

    assert nuevo.estado == EstadoTicket.CERRADO
    assert nuevo.peso_neto == 33100


def test_ticket_inexistente_devuelve_none(session):
    assert TicketRepository(session).get_ticket_by_id(999999) is None


def test_update_ticket_lo_cierra(session, proveedor):
    repo = TicketRepository(session)
    ticket = repo.create_ticket(crear_ticket(proveedor))

    ticket.peso_bruto = 45000
    ticket.estado = EstadoTicket.CERRADO
    actualizado = repo.update_ticket(ticket)

    assert actualizado.peso_neto == 29840
    assert repo.get_ticket_by_id(ticket.id).estado == EstadoTicket.CERRADO


def test_update_ticket_inexistente_devuelve_none(session, proveedor):
    ticket = crear_ticket(proveedor)
    ticket.id = 999999
    assert TicketRepository(session).update_ticket(ticket) is None


def test_get_all_tickets_filtra_por_estado(session, proveedor):
    repo = TicketRepository(session)
    abierto = repo.create_ticket(crear_ticket(proveedor))
    cerrado = repo.create_ticket(crear_ticket(proveedor, 48260, EstadoTicket.CERRADO))

    ids_abiertos = [t.id for t in repo.get_all_tickets(EstadoTicket.ABIERTO)]
    ids_cerrados = [t.id for t in repo.get_all_tickets(EstadoTicket.CERRADO)]
    ids_todos = [t.id for t in repo.get_all_tickets()]

    assert abierto.id in ids_abiertos and cerrado.id not in ids_abiertos
    assert cerrado.id in ids_cerrados and abierto.id not in ids_cerrados
    assert abierto.id in ids_todos and cerrado.id in ids_todos