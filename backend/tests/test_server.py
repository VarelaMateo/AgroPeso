from datetime import date

import pytest

from models.products import ProductEntity
from models.suppliers import SupplierEntity
from models.ticket_model import EstadoTicket, Ticket
from services.ticket_service import TicketService
from utils.exceptions import ReferenciaNoEncontradaError, ReglaNegocioError, TicketNoEncontradoError
from models.user_model import Rol, UsuarioActual

ADMIN = UsuarioActual(username="admin_test", rol=Rol.ADMIN)

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

    def get_all_tickets(self, estado=None, supplier_id=None):
        tickets = list(self.tickets.values())   # usá cómo guardás los tickets
        if estado is not None:
            tickets = [t for t in tickets if t.estado == estado]
        if supplier_id is not None:
            tickets = [t for t in tickets if t.supplier_id == supplier_id]
        return tickets


class ProveedoresEnMemoria:
    def __init__(self):
        self.proveedores = {1: SupplierEntity(name="Berg", id=1), 2: SupplierEntity(name="Otro", id=2)}

    def get_supplier_by_id(self, supplier_id):
        return self.proveedores.get(supplier_id)


class ProductosEnMemoria:
    def __init__(self):
        self.productos = {1: ProductEntity(name="Soja", id=1)}

    def get_product_by_id(self, product_id):
        return self.productos.get(product_id)


def crear_ticket(tara, bruto, supplier_id=1):
    return Ticket(date.today(), "Ivan Derio", "HKN279", tara, bruto, supplier_id)


@pytest.fixture
def service():
    return TicketService(RepositorioEnMemoria(), ProveedoresEnMemoria(), ProductosEnMemoria())


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


def test_registrar_con_proveedor_inexistente_lanza_error_y_no_guarda(service):
    with pytest.raises(ReglaNegocioError, match="proveedor"):
        service.registrar_pesada(crear_ticket(15160, None, supplier_id=999))
    assert service.obtener_todos_los_tickets(ADMIN) == []


def test_registrar_con_producto_existente(service):
    ticket = crear_ticket(15160, None)
    ticket.product_id = 1
    assert service.registrar_pesada(ticket).product_id == 1


def test_registrar_con_producto_inexistente_lanza_error_y_no_guarda(service):
    ticket = crear_ticket(15160, None)
    ticket.product_id = 999
    with pytest.raises(ReglaNegocioError, match="producto"):
        service.registrar_pesada(ticket)
    assert service.obtener_todos_los_tickets(ADMIN) == []


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
    assert len(service.obtener_todos_los_tickets(ADMIN)) == 2


def test_obtener_todos_filtra_por_estado(service):
    service.registrar_pesada(crear_ticket(15160, None))
    service.registrar_pesada(crear_ticket(15160, 48260))
    service.registrar_pesada(crear_ticket(14300, None))

    abiertos = service.obtener_todos_los_tickets(ADMIN, estado=EstadoTicket.ABIERTO)
    cerrados = service.obtener_todos_los_tickets(ADMIN, estado=EstadoTicket.CERRADO)

    assert len(abiertos) == 2
    assert all(t.estado == EstadoTicket.ABIERTO for t in abiertos)
    assert len(cerrados) == 1

 # --- Autorización por rol ---

def test_cliente_solo_ve_tickets_de_su_proveedor(service):
    service.registrar_pesada(crear_ticket(15160, None, supplier_id=1))
    service.registrar_pesada(crear_ticket(15160, 48260, supplier_id=1))
    service.registrar_pesada(crear_ticket(14300, None, supplier_id=2))

    cliente = UsuarioActual(username="cliente_test", rol=Rol.CLIENTE, supplier_id=1)
    tickets = service.obtener_todos_los_tickets(cliente)

    assert len(tickets) == 2
    assert all(t.supplier_id == 1 for t in tickets)


def test_admin_ve_tickets_de_todos_los_proveedores(service):
    service.registrar_pesada(crear_ticket(15160, None, supplier_id=1))
    service.registrar_pesada(crear_ticket(14300, None, supplier_id=2))
    assert len(service.obtener_todos_los_tickets(ADMIN)) == 2


def test_cliente_sin_proveedor_no_ve_nada(service):
    service.registrar_pesada(crear_ticket(15160, None, supplier_id=1))
    sin_proveedor = UsuarioActual(username="cliente_test", rol=Rol.CLIENTE, supplier_id=None)
    assert service.obtener_todos_los_tickets(sin_proveedor) == []


def test_cliente_puede_ver_su_propio_ticket_por_id(service):
    ticket = service.registrar_pesada(crear_ticket(15160, None, supplier_id=1))
    cliente = UsuarioActual(username="cliente_test", rol=Rol.CLIENTE, supplier_id=1)
    assert service.obtener_ticket_de_usuario(ticket.id, cliente).id == ticket.id


def test_cliente_no_puede_ver_ticket_de_otro_proveedor(service):
    ajeno = service.registrar_pesada(crear_ticket(15160, None, supplier_id=2))
    cliente = UsuarioActual(username="cliente_test", rol=Rol.CLIENTE, supplier_id=1)
    with pytest.raises(TicketNoEncontradoError):
        service.obtener_ticket_de_usuario(ajeno.id, cliente)


def test_admin_puede_ver_cualquier_ticket_por_id(service):
    ticket = service.registrar_pesada(crear_ticket(15160, None, supplier_id=2))
    assert service.obtener_ticket_de_usuario(ticket.id, ADMIN).id == ticket.id

# --- Editar ticket ---

def editar(service, ticket_id, **cambios):
    datos = {"chofer": "Ivan Derio", "patente": "HKN279", "peso_tara": 15160, "peso_bruto": None,
             "supplier_id": 1, "product_id": None}
    datos.update(cambios)
    return service.editar_ticket(ticket_id, **datos)


def test_editar_ticket_abierto_corrige_datos_y_sigue_abierto(service):
    abierto = service.registrar_pesada(crear_ticket(15160, None))
    editado = editar(service, abierto.id, chofer="Juan Perez", patente="AB123CD",
                     peso_tara=15000, supplier_id=2, product_id=1)
    assert editado.estado == EstadoTicket.ABIERTO
    assert (editado.chofer, editado.patente, editado.peso_tara) == ("Juan Perez", "AB123CD", 15000)
    assert (editado.supplier_id, editado.product_id) == (2, 1)
    assert editado.peso_neto is None


def test_editar_ticket_abierto_con_bruto_lo_cierra(service):
    abierto = service.registrar_pesada(crear_ticket(15160, None))
    editado = editar(service, abierto.id, peso_bruto=48260)
    assert editado.estado == EstadoTicket.CERRADO
    assert editado.peso_neto == 33100


def test_editar_ticket_cerrado_recalcula_el_neto(service):
    cerrado = service.registrar_pesada(crear_ticket(15160, 48260))
    editado = editar(service, cerrado.id, peso_tara=16000, peso_bruto=50000)
    assert editado.estado == EstadoTicket.CERRADO
    assert editado.peso_neto == 34000


@pytest.mark.parametrize("bruto", [15160, 10000])
def test_editar_con_bruto_menor_o_igual_a_la_tara_lanza_error_y_no_cambia(service, bruto):
    cerrado = service.registrar_pesada(crear_ticket(15160, 48260))
    with pytest.raises(ReglaNegocioError):
        editar(service, cerrado.id, chofer="Otro", peso_bruto=bruto)
    guardado = service.obtener_ticket(cerrado.id)
    assert (guardado.chofer, guardado.peso_bruto) == ("Ivan Derio", 48260)


def test_editar_ticket_cerrado_sin_bruto_lanza_error(service):
    cerrado = service.registrar_pesada(crear_ticket(15160, 48260))
    with pytest.raises(ReglaNegocioError):
        editar(service, cerrado.id, peso_bruto=None)
    assert service.obtener_ticket(cerrado.id).estado == EstadoTicket.CERRADO


def test_editar_ticket_inexistente_lanza_error(service):
    with pytest.raises(TicketNoEncontradoError):
        editar(service, 999)


def test_editar_con_proveedor_o_producto_inexistente_lanza_error(service):
    abierto = service.registrar_pesada(crear_ticket(15160, None))
    with pytest.raises(ReferenciaNoEncontradaError):
        editar(service, abierto.id, supplier_id=99)
    with pytest.raises(ReferenciaNoEncontradaError):
        editar(service, abierto.id, product_id=99)
    assert service.obtener_ticket(abierto.id).supplier_id == 1
