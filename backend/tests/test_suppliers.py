import pytest
from pydantic import ValidationError

from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository
from schemas.supplier_schema import SupplierCreate, SupplierResponse
from services.supplier_service import SupplierService
from models.user_model import Rol, UsuarioActual
from utils.exceptions import ProveedorDuplicadoError


# --- Esquemas ---

def test_supplier_create_limpia_espacios():
    assert SupplierCreate(name="  Berg  ").name == "Berg"


@pytest.mark.parametrize("nombre", ["", "   "])
def test_supplier_create_rechaza_nombre_vacio(nombre):
    with pytest.raises(ValidationError):
        SupplierCreate(name=nombre)


def test_supplier_create_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        SupplierCreate(name="Berg", id=5)


def test_supplier_response_desde_entidad():
    respuesta = SupplierResponse.model_validate(SupplierEntity(name="Berg", id=3))
    assert (respuesta.id, respuesta.name) == (3, "Berg")


# --- Servicio (repositorio en memoria) ---

class RepositorioEnMemoria:
    def __init__(self):
        self.proveedores = []

    def create_supplier(self, supplier):
        supplier.id = len(self.proveedores) + 1
        self.proveedores.append(supplier)
        return supplier

    def get_all_suppliers(self):
        return list(self.proveedores)

    def get_supplier_by_name(self, name):
        return next((s for s in self.proveedores if s.name.lower() == name.lower()), None)


def test_servicio_crea_y_lista_proveedores():
    service = SupplierService(RepositorioEnMemoria())
    creado = service.crear_proveedor(SupplierEntity(name="Berg"))
    admin = UsuarioActual(username="admin_test", rol=Rol.ADMIN)
    assert creado.id == 1
    assert service.obtener_todos_los_proveedores(admin) == [creado]

def test_cliente_solo_ve_su_proveedor():
    service = SupplierService(RepositorioEnMemoria())
    service.crear_proveedor(SupplierEntity(name="Berg"))
    service.crear_proveedor(SupplierEntity(name="Otro"))
    cliente = UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1)
    visibles = service.obtener_todos_los_proveedores(cliente)
    assert [s.id for s in visibles] == [1]
    
@pytest.mark.parametrize("nombre", ["Berg", "BERG", "berg"])
def test_servicio_rechaza_proveedor_duplicado(nombre):
    service = SupplierService(RepositorioEnMemoria())
    service.crear_proveedor(SupplierEntity(name="Berg"))
    with pytest.raises(ProveedorDuplicadoError):
        service.crear_proveedor(SupplierEntity(name=nombre))
    admin = UsuarioActual(username="admin_test", rol=Rol.ADMIN)
    assert len(service.obtener_todos_los_proveedores(admin)) == 1

# --- Repositorio (base real, se deshace con rollback) ---

def test_repositorio_crea_y_lista(session):
    repo = SupplierRepository(session)
    creado = repo.create_supplier(SupplierEntity(name="Proveedor Test"))
    assert creado.id is not None
    assert creado in repo.get_all_suppliers()


def test_repositorio_busca_por_id(session, proveedor):
    repo = SupplierRepository(session)
    assert repo.get_supplier_by_id(proveedor.id).name == "Proveedor de prueba"
    assert repo.get_supplier_by_id(999999) is None


def test_repositorio_busca_por_nombre_sin_distinguir_mayusculas(session, proveedor):
    repo = SupplierRepository(session)
    assert repo.get_supplier_by_name("PROVEEDOR DE PRUEBA").id == proveedor.id
    assert repo.get_supplier_by_name("No existe") is None
