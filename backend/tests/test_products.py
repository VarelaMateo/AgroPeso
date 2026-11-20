import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from models.products import ProductEntity
from repository.product_repository import ProductRepository
from schemas.product_schema import ProductCreate, ProductResponse
from services.product_service import ProductService
from utils.exceptions import ProductoDuplicadoError


# --- Esquemas ---

def test_product_create_limpia_espacios():
    assert ProductCreate(name="  Soja  ").name == "Soja"


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 201])
def test_product_create_rechaza_nombre_invalido(nombre):
    with pytest.raises(ValidationError):
        ProductCreate(name=nombre)


def test_product_create_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        ProductCreate(name="Soja", id=5)


def test_product_response_desde_entidad():
    respuesta = ProductResponse.model_validate(ProductEntity(name="Soja", id=3))
    assert (respuesta.id, respuesta.name) == (3, "Soja")


# --- Servicio (repositorio en memoria) ---

class RepositorioEnMemoria:
    def __init__(self):
        self.productos = []

    def create_product(self, product):
        product.id = len(self.productos) + 1
        self.productos.append(product)
        return product

    def get_all_products(self):
        return list(self.productos)

    def get_product_by_name(self, name):
        return next((p for p in self.productos if p.name.lower() == name.lower()), None)


def test_servicio_crea_y_lista_productos():
    service = ProductService(RepositorioEnMemoria())
    creado = service.crear_producto(ProductEntity(name="Soja"))
    assert creado.id == 1
    assert service.obtener_todos_los_productos() == [creado]


@pytest.mark.parametrize("nombre", ["Soja", "SOJA", "soja"])
def test_servicio_rechaza_producto_duplicado(nombre):
    service = ProductService(RepositorioEnMemoria())
    service.crear_producto(ProductEntity(name="Soja"))
    with pytest.raises(ProductoDuplicadoError):
        service.crear_producto(ProductEntity(name=nombre))
    assert len(service.obtener_todos_los_productos()) == 1


# --- Repositorio (base real, se deshace con rollback) ---

def test_repositorio_crea_y_lista(session):
    repo = ProductRepository(session)
    creado = repo.create_product(ProductEntity(name="Producto Test"))
    assert creado.id is not None
    assert creado in repo.get_all_products()


def test_repositorio_busca_por_id(session, producto):
    repo = ProductRepository(session)
    assert repo.get_product_by_id(producto.id).name == "Producto de prueba"
    assert repo.get_product_by_id(999999) is None


def test_repositorio_busca_por_nombre_sin_distinguir_mayusculas(session, producto):
    repo = ProductRepository(session)
    assert repo.get_product_by_name("PRODUCTO DE PRUEBA").id == producto.id
    assert repo.get_product_by_name("No existe") is None


class SesionQueChocaConUnique:
    """Simula que otra petición insertó el mismo nombre justo antes del commit."""
    def __init__(self):
        self.hizo_rollback = False

    def add(self, objeto):
        pass

    def commit(self):
        raise IntegrityError("INSERT", {}, Exception("Duplicate entry"))

    def rollback(self):
        self.hizo_rollback = True


def test_repositorio_traduce_integrity_error_a_duplicado():
    sesion = SesionQueChocaConUnique()
    with pytest.raises(ProductoDuplicadoError):
        ProductRepository(sesion).create_product(ProductEntity(name="Soja"))
    assert sesion.hizo_rollback
