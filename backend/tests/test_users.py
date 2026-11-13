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