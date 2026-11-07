from datetime import date

import pytest

from models.ticket_model import EstadoTicket, Ticket
from services.ticket_service import TicketService
from utils.exceptions import ReglaNegocioError, TicketNoEncontradoError


class RepositorioEnMemoria:
    def __init__(self):
        self.tickets = {}
        self.siguiente_id = 1

    def create_ticket(self, ticket):
        ticket.id = self.siguiente_id
        self.siguiente_id += 1
        self.tickets[ticket.id] = ticket
        return ticket

    def get_ticket_by_id(self, ticket_id):
        return self.tickets.get(ticket_id)

    def update_ticket(self, ticket):
        self.tickets[ticket.id] = ticket
        return ticket

    def get_all_tickets(self, estado=None):
        return [t for t in self.tickets.values() if estado is None or t.estado == estado]


def crear_ticket(tara, bruto):
    return Ticket(date.today(), "Ivan Derio", "HKN279", tara, bruto, 1)


@pytest.fixture
def service():
    return TicketService(RepositorioEnMemoria())


# --- Entidad ---

def test_ticket_acepta_estado_y_calcula_neto():
    abierto = Ticket(date.today(), "Ivan Derio", "HKN279", 15160, None, 1,
                     estado=EstadoTicket.ABIERTO)
    assert abierto.estado == EstadoTicket.ABIERTO
    assert abierto.peso_neto is None

    cerrado = Ticket(date.today(), "Ivan Derio", "HKN279", 15160, 48260, 1,
                     estado=EstadoTicket.CERRADO)
    assert cerrado.peso_neto == 33100


# --- Registrar pesada ---

def test_registrar_sin_bruto_abre_el_ticket(service):
    ticket = service.registrar_pesada(crear_ticket(15160, None))
    assert ticket.id == 1
    assert ticket.estado == EstadoTicket.ABIERTO
    assert ticket.peso_neto is None


def test_registrar_con_bruto_cierra_el_ticket(service):
    ticket = service.registrar_pesada(crear_ticket(15160, 48260))
    assert ticket.estado == EstadoTicket.CERRADO
    assert ticket.peso_neto == 33100


def test_registrar_con_bruto_menor_a_la_tara_lanza_error(service):
    with pytest.raises(ReglaNegocioError):
        service.registrar_pesada(crear_ticket(48260, 15160))


def test_registrar_con_bruto_igual_a_la_tara_lanza_error(service):
    with pytest.raises(ReglaNegocioError):
        service.registrar_pesada(crear_ticket(15160, 15160))


# --- Cerrar ticket ---

def test_cerrar_ticket_abierto(service):
    abierto = service.registrar_pesada(crear_ticket(15160, None))
    cerrado = service.cerrar_ticket(abierto.id, 48260)
    assert cerrado.estado == EstadoTicket.CERRADO
    assert cerrado.peso_bruto == 48260
    assert cerrado.peso_neto == 33100


def test_cerrar_ticket_ya_cerrado_lanza_error(service):
    cerrado = service.registrar_pesada(crear_ticket(15160, 48260))
    with pytest.raises(ReglaNegocioError):
        service.cerrar_ticket(cerrado.id, 50000)


def test_cerrar_con_bruto_invalido_lanza_error_y_sigue_abierto(service):
    abierto = service.registrar_pesada(crear_ticket(15160, None))
    with pytest.raises(ReglaNegocioError):
        service.cerrar_ticket(abierto.id, 15160)
    assert service.obtener_ticket(abierto.id).estado == EstadoTicket.ABIERTO


def test_cerrar_ticket_inexistente_lanza_error(service):
    with pytest.raises(TicketNoEncontradoError):
        service.cerrar_ticket(999, 48260)


# --- Obtener y listar ---

def test_obtener_ticket_inexistente_lanza_error(service):
    with pytest.raises(TicketNoEncontradoError):
        service.obtener_ticket(999)


def test_obtener_todos_sin_filtro(service):
    service.registrar_pesada(crear_ticket(15160, None))
    service.registrar_pesada(crear_ticket(15160, 48260))
    assert len(service.obtener_todos_los_tickets()) == 2


def test_obtener_todos_filtra_por_estado(service):
    service.registrar_pesada(crear_ticket(15160, None))
    service.registrar_pesada(crear_ticket(15160, 48260))
    service.registrar_pesada(crear_ticket(14300, None))

    abiertos = service.obtener_todos_los_tickets(EstadoTicket.ABIERTO)
    cerrados = service.obtener_todos_los_tickets(EstadoTicket.CERRADO)

    assert len(abiertos) == 2
    assert all(t.estado == EstadoTicket.ABIERTO for t in abiertos)
    assert len(cerrados) == 1