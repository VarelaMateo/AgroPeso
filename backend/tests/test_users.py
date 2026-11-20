import pytest
from pydantic import ValidationError

from models.user_model import Rol, User
from repository.user_repository import UserRepository
from schemas.user_schema import UserCreate


def test_crear_y_buscar_cliente(session, proveedor):
    repo = UserRepository(session)
    creado = repo.create_user(
        User(username="cliente_test", password_hash="hash-falso", rol=Rol.CLIENTE, supplier_id=proveedor.id)
    )
    assert creado.id is not None

    encontrado = repo.get_user_by_username("cliente_test")
    assert encontrado.rol == Rol.CLIENTE
    assert encontrado.supplier_id == proveedor.id


def test_crear_admin_sin_proveedor(session):
    repo = UserRepository(session)
    creado = repo.create_user(User(username="admin_test", password_hash="hash-falso", rol=Rol.ADMIN))
    assert creado.supplier_id is None


def test_usuario_inexistente_devuelve_none(session):
    assert UserRepository(session).get_user_by_username("nadie") is None


def test_cliente_sin_proveedor_es_invalido():
    with pytest.raises(ValidationError):
        UserCreate(username="berg1", password="secreto1", rol="cliente")


def test_admin_con_proveedor_es_invalido():
    with pytest.raises(ValidationError):
        UserCreate(username="admin", password="secreto1", rol="admin", supplier_id=1)


def test_rol_desconocido_es_invalido():
    with pytest.raises(ValidationError):
        UserCreate(username="x1x", password="secreto1", rol="superman")

# --- AGROPESO-024: alta de clientes ---

from sqlalchemy.exc import IntegrityError

from models.suppliers import SupplierEntity
from schemas.user_schema import ClienteCreate
from services.auth_service import verify_password
from services.user_service import UserService
from utils.exceptions import ReglaNegocioError, UsuarioDuplicadoError


def test_cliente_create_recorta_usuario_pero_no_la_contrasena():
    datos = ClienteCreate(username="  berg  ", password=" clave1 ", supplier_id=1)
    assert datos.username == "berg"
    assert datos.password == " clave1 "


@pytest.mark.parametrize("cambios", [
    {"username": "ab"},              # usuario corto
    {"username": "   ab   "},        # corto después de recortar
    {"username": "x" * 51},          # usuario largo
    {"password": "12345"},           # contraseña corta
    {"password": "ñ" * 37},          # 74 bytes: supera el límite de bcrypt
    {"supplier_id": 0},              # proveedor inválido
    {"rol": "admin"},                # el rol no se puede enviar
])
def test_cliente_create_rechaza_datos_invalidos(cambios):
    datos = {"username": "berg", "password": "clave123", "supplier_id": 1, **cambios}
    with pytest.raises(ValidationError):
        ClienteCreate(**datos)


class UsuariosEnMemoria:
    def __init__(self):
        self.usuarios = []

    def get_user_by_username(self, username):
        return next((u for u in self.usuarios if u.username.lower() == username.lower()), None)

    def create_user(self, user):
        user.id = len(self.usuarios) + 1
        self.usuarios.append(user)
        return user


class ProveedoresEnMemoria:
    def get_supplier_by_id(self, supplier_id):
        return SupplierEntity(name="Berg", id=1) if supplier_id == 1 else None


@pytest.fixture
def user_service():
    return UserService(UsuariosEnMemoria(), ProveedoresEnMemoria())


def test_servicio_crea_cliente_con_hash(user_service):
    creado = user_service.crear_cliente("berg", "clave123", 1)
    assert creado.rol == Rol.CLIENTE
    assert creado.supplier_id == 1
    assert creado.password_hash != "clave123"
    assert verify_password("clave123", creado.password_hash)


@pytest.mark.parametrize("nombre", ["berg", "BERG"])
def test_servicio_rechaza_usuario_duplicado(user_service, nombre):
    user_service.crear_cliente("berg", "clave123", 1)
    with pytest.raises(UsuarioDuplicadoError):
        user_service.crear_cliente(nombre, "otraclave", 1)


def test_servicio_rechaza_proveedor_inexistente(user_service):
    with pytest.raises(ReglaNegocioError, match="proveedor"):
        user_service.crear_cliente("berg", "clave123", 999)


class SesionQueChocaConUnique:
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
    with pytest.raises(UsuarioDuplicadoError):
        UserRepository(sesion).create_user(User(username="berg", password_hash="h", rol=Rol.CLIENTE, supplier_id=1))
    assert sesion.hizo_rollback
