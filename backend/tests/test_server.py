from datetime import date

import pytest

from models.ticket_model import Ticket
from services.ticket_service import TicketService
from utils.exceptions import ReglaNegocioError, TicketNoEncontradoError

#pytest.raises(...) reemplaza los try/except que usábamos antes.


class RepositorioFalso:
    def create_ticket(self, ticket):
        ticket.id = 1
        return ticket

    def get_ticket_by_id(self, ticket_id):
        return None


def crear_ticket(tara, bruto):
    return Ticket(date.today(), "Ivan Derio", "HKN279", tara, bruto, 1)


def test_registrar_pesada_valida():
    service = TicketService(RepositorioFalso())
    resultado = service.registrar_pesada(crear_ticket(15160, 48260))
    assert resultado.id == 1


def test_bruto_menor_a_la_tara_lanza_error():
    service = TicketService(RepositorioFalso())
    with pytest.raises(ReglaNegocioError):
        service.registrar_pesada(crear_ticket(48260, 15160))


def test_ticket_inexistente_lanza_error():
    service = TicketService(RepositorioFalso())
    with pytest.raises(TicketNoEncontradoError):
        service.obtener_ticket(999)