import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from config.database import get_db
from main import app
from middleware.security import get_current_user
from models.user_model import Rol, User, UsuarioActual
from repository.user_repository import UserRepository
from routers import auth_router
from schemas.ticket_schema import TicketCreate
from schemas.user_schema import ClienteCreate
from services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar():
    auth_router._fallidos.clear()
    yield
    auth_router._fallidos.clear()
    app.dependency_overrides.clear()


def login(usuario, clave):
    return client.post("/auth/login", data={"username": usuario, "password": clave})


# --- Fuerza bruta en el login ---

def test_login_se_bloquea_despues_de_5_fallos(session):
    app.dependency_overrides[get_db] = lambda: session
    for _ in range(auth_router.MAX_FALLIDOS):
        assert login("no_existe_test", "incorrecta").status_code == 401
    r = login("No_Existe_Test", "incorrecta")  # mismo usuario aunque cambien las mayúsculas
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0


def test_login_correcto_reinicia_los_fallos(session):
    app.dependency_overrides[get_db] = lambda: session
    UserRepository(session).create_user(
        User(username="seguridad_test", password_hash=auth_service.get_password_hash("clave-segura"), rol=Rol.ADMIN))
    for _ in range(auth_router.MAX_FALLIDOS - 1):
        login("seguridad_test", "mal")
    assert login("seguridad_test", "clave-segura").status_code == 200
    for _ in range(auth_router.MAX_FALLIDOS - 1):
        assert login("seguridad_test", "mal").status_code == 401  # el contador volvió a cero


def test_usuario_inexistente_igual_verifica_un_hash(monkeypatch):
    # Así tarda lo mismo que con un usuario real y no se puede adivinar qué usuarios existen
    llamadas = []
    monkeypatch.setattr(auth_service, "verify_password", lambda clave, hash_: llamadas.append(hash_) or False)

    class SinUsuarios:
        def get_user_by_username(self, username):
            return None

    assert auth_service.authenticate_user(SinUsuarios(), "nadie", "clave") is None
    assert llamadas == [auth_service._HASH_DE_RELLENO]


def test_clave_demasiado_larga_no_se_hashea(monkeypatch):
    monkeypatch.setattr(auth_service, "verify_password", lambda *a: pytest.fail("no debería hashear"))
    assert auth_service.authenticate_user(None, "admin", "x" * 1000) is None


# --- Cabeceras y CORS ---

def test_respuestas_con_cabeceras_de_seguridad():
    r = client.get("/tickets/")  # 401, pero igual con las cabeceras
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"


def test_cors_solo_metodos_y_headers_usados():
    r = client.options("/tickets/", headers={
        "Origin": "http://localhost:5500",
        "Access-Control-Request-Method": "DELETE",
        "Access-Control-Request-Headers": "authorization",
    })
    assert r.status_code == 200
    assert "access-control-allow-credentials" not in r.headers
    r = client.options("/tickets/", headers={
        "Origin": "http://localhost:5500",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "x-otro-header",
    })
    assert r.status_code == 400


def test_origen_no_permitido_no_recibe_cors():
    r = client.get("/tickets/", headers={"Origin": "https://sitio-malicioso.example"})
    assert "access-control-allow-origin" not in r.headers


# --- Validación de entrada ---

@pytest.mark.parametrize("clave", ["corta1", "berg_cliente", "BERG_CLIENTE  "])
def test_clave_de_cliente_corta_o_igual_al_usuario(clave):
    with pytest.raises(ValidationError):
        ClienteCreate(username="berg_cliente", password=clave, supplier_id=1)


def test_peso_mayor_al_tope_de_la_base_responde_422():
    app.dependency_overrides[get_current_user] = lambda: UsuarioActual(username="a", rol=Rol.ADMIN)
    r = client.post("/tickets/", json={"chofer": "x", "peso_tara": 3_000_000_000, "supplier_id": 1})
    assert r.status_code == 422
    with pytest.raises(ValidationError):
        TicketCreate(chofer="x", peso_tara=1, supplier_id=1, numero_ticket=0)
