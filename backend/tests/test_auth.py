import jwt
import pytest

from models.user_model import Rol, User
from services import auth_service

CLAVE = "clave-de-test-bastante-larga-para-hmac-1234567890"


@pytest.fixture(autouse=True)
def clave_de_prueba(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", CLAVE)


class RepoFalso:
    def __init__(self, *usuarios):
        self.usuarios = {u.username: u for u in usuarios}

    def get_user_by_username(self, username):
        return self.usuarios.get(username)


def test_hash_no_es_texto_plano_y_se_verifica():
    hashed = auth_service.get_password_hash("secreto1")
    assert hashed != "secreto1"
    assert auth_service.verify_password("secreto1", hashed)
    assert not auth_service.verify_password("otra-clave", hashed)


def test_dos_hashes_de_la_misma_clave_son_distintos():
    assert auth_service.get_password_hash("secreto1") != auth_service.get_password_hash("secreto1")


def test_token_contiene_username_rol_y_supplier_id():
    token = auth_service.create_access_token({"username": "berg1", "rol": "cliente", "supplier_id": 7})
    datos = jwt.decode(token, CLAVE, algorithms=["HS256"])
    assert datos["username"] == "berg1"
    assert datos["rol"] == "cliente"
    assert datos["supplier_id"] == 7
    assert "exp" in datos


def test_autenticar_usuario_correcto():
    user = User(username="admin", password_hash=auth_service.get_password_hash("secreto1"), rol=Rol.ADMIN)
    assert auth_service.authenticate_user(RepoFalso(user), "admin", "secreto1") is user


def test_autenticar_con_clave_incorrecta_o_usuario_inexistente():
    user = User(username="admin", password_hash=auth_service.get_password_hash("secreto1"), rol=Rol.ADMIN)
    repo = RepoFalso(user)
    assert auth_service.authenticate_user(repo, "admin", "mala") is None
    assert auth_service.authenticate_user(repo, "nadie", "secreto1") is None