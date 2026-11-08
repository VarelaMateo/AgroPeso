import pytest
from pydantic import ValidationError

from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository
from schemas.supplier_schema import SupplierCreate, SupplierResponse
from services.supplier_service import SupplierService


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


def test_servicio_crea_y_lista_proveedores():
    service = SupplierService(RepositorioEnMemoria())
    creado = service.crear_proveedor(SupplierEntity(name="Berg"))
    assert creado.id == 1
    assert service.obtener_todos_los_proveedores() == [creado]


# --- Repositorio (base real, se deshace con rollback) ---

def test_repositorio_crea_y_lista(session):
    repo = SupplierRepository(session)
    creado = repo.create_supplier(SupplierEntity(name="Proveedor Test"))
    assert creado.id is not None
    assert creado in repo.get_all_suppliers()