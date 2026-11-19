from fastapi.testclient import TestClient

from main import app
from middleware.security import get_current_user
from models.user_model import Rol, UsuarioActual

client = TestClient(app)

TICKET = {"chofer": "Ivan Derio", "peso_tara": 15160, "supplier_id": 1}


def como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


def teardown_function():
    app.dependency_overrides.clear()


def test_sin_token_responde_401():
    assert client.get("/tickets/").status_code == 401
    assert client.post("/tickets/", json=TICKET).status_code == 401
    assert client.get("/suppliers/").status_code == 401


def test_token_invalido_responde_401():
    r = client.get("/tickets/", headers={"Authorization": "Bearer abc"})
    assert r.status_code == 401


def test_cliente_no_puede_crear_ticket():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/tickets/", json=TICKET).status_code == 403


def test_cliente_no_puede_cerrar_ticket():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.patch("/tickets/1/cerrar", json={"peso_bruto": 48260}).status_code == 403


def test_cliente_no_puede_crear_proveedor():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/suppliers/", json={"name": "Berg"}).status_code == 403