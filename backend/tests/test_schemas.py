from datetime import date

import pytest
from pydantic import ValidationError

from models.ticket_model import EstadoTicket, Ticket
from schemas.ticket_schema import TicketCreate, TicketClose, TicketResponse

#assert: Comprueban si una condición es Verdadera durante la ejecución
def test_ticket_create_valido():
    t = TicketCreate(
        chofer="Ivan Derio", patente="HKN279",
        peso_tara=15160, peso_bruto=48260, supplier_id=1,
    )
    assert t.transporte == "Equipo"
    assert t.numero_ticket is None


def test_ticket_create_rechaza_peso_negativo():
    with pytest.raises(ValidationError):
        TicketCreate(chofer="Ivan Derio", peso_tara=-1, peso_bruto=48260, supplier_id=1)


def test_ticket_response_desde_entidad():
    ticket = Ticket(date.today(), "Ivan Derio", "HKN279", 15160, 48260, 1, id=5)
    respuesta = TicketResponse.model_validate(ticket)
    assert respuesta.id == 5
    assert respuesta.peso_neto == 33100

def test_ticket_create_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        TicketCreate(chofer="Ivan Derio", peso_tara=1, peso_bruto=2, supplier_id=1, id=99)


def test_ticket_create_limpia_espacios():
    t = TicketCreate(chofer="  Ivan Derio  ", peso_tara=1, peso_bruto=2, supplier_id=1)
    assert t.chofer == "Ivan Derio"

def test_ticket_create_sin_peso_bruto_es_valido():
    t = TicketCreate(chofer="Ivan Derio", peso_tara=15160, supplier_id=1)
    assert t.peso_bruto is None


def test_ticket_create_rechaza_estado():
    with pytest.raises(ValidationError):
        TicketCreate(chofer="Ivan Derio", peso_tara=15160, supplier_id=1, estado="cerrado")


def test_ticket_response_de_ticket_abierto():
    ticket = Ticket(date.today(), "Ivan Derio", "HKN279", 15160, None, 1, id=7)
    respuesta = TicketResponse.model_validate(ticket)
    assert respuesta.estado == EstadoTicket.ABIERTO
    assert respuesta.peso_bruto is None
    assert respuesta.peso_neto is None


def test_ticket_close_valido():
    assert TicketClose(peso_bruto=48260).peso_bruto == 48260


@pytest.mark.parametrize("valor", [0, -5])
def test_ticket_close_rechaza_pesos_no_positivos(valor):
    with pytest.raises(ValidationError):
        TicketClose(peso_bruto=valor)


def test_ticket_close_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        TicketClose(peso_bruto=48260, estado="cerrado")