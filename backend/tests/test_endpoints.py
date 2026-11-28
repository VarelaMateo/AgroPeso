from datetime import date, timedelta

from fastapi.testclient import TestClient

from config.database import get_db
from main import app
from middleware.security import get_current_user
from models.user_model import Rol, UsuarioActual
from repository.user_repository import UserRepository

client = TestClient(app)

TICKET = {"chofer": "Ivan Derio", "peso_tara": 15160, "supplier_id": 1}
CLIENTE = {"username": "cliente_api_test", "password": "clave123", "supplier_id": 1}


ADMIN_SIN_BD = UsuarioActual(username="admin_test", rol=Rol.ADMIN)


def como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


def teardown_function():
    app.dependency_overrides.clear()


def test_sin_token_responde_401():
    assert client.get("/tickets/").status_code == 401
    assert client.post("/tickets/", json=TICKET).status_code == 401
    assert client.get("/suppliers/").status_code == 401
    assert client.get("/products/").status_code == 401
    assert client.post("/products/", json={"name": "Soja"}).status_code == 401
    assert client.post("/users/", json=CLIENTE).status_code == 401
    assert client.put("/tickets/1", json=TICKET).status_code == 401


def test_token_invalido_responde_401():
    r = client.get("/tickets/", headers={"Authorization": "Bearer abc"})
    assert r.status_code == 401


def test_cliente_no_puede_crear_ticket():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/tickets/", json=TICKET).status_code == 403


def test_cliente_no_puede_cerrar_ticket():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.patch("/tickets/1/cerrar", json={"peso_bruto": 48260}).status_code == 403


def test_cliente_no_puede_editar_ticket():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.put("/tickets/1", json=TICKET).status_code == 403


def test_editar_ticket_no_acepta_campos_extra():
    como(ADMIN_SIN_BD)
    assert client.put("/tickets/1", json={**TICKET, "peso_neto": 5}).status_code == 422


def test_cliente_no_puede_crear_proveedor():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/suppliers/", json={"name": "Berg"}).status_code == 403


def test_cliente_no_puede_crear_usuarios():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/users/", json=CLIENTE).status_code == 403
    assert client.put("/users/", json=CLIENTE).status_code == 403
    assert client.delete("/users/berg?supplier_id=1").status_code == 403


def test_alta_de_cliente_no_acepta_rol():
    como(ADMIN_SIN_BD)
    assert client.post("/users/", json={**CLIENTE, "rol": "admin"}).status_code == 422


def test_cliente_no_puede_crear_producto():
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    assert client.post("/products/", json={"name": "Soja"}).status_code == 403


# --- Validaciones de proveedores (base real, se deshace con rollback) ---

ADMIN = UsuarioActual(username="admin_test", rol=Rol.ADMIN)


def usar_sesion(session):
    app.dependency_overrides[get_db] = lambda: session


def test_proveedor_duplicado_responde_409(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/suppliers/", json={"name": "PROVEEDOR DE PRUEBA"})
    assert r.status_code == 409
    assert "Ya existe" in r.json()["detail"]


def test_ticket_con_proveedor_inexistente_responde_400(session):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/tickets/", json={**TICKET, "supplier_id": 999999})
    assert r.status_code == 400
    assert "proveedor" in r.json()["detail"]


def test_ticket_con_proveedor_existente_responde_201(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/tickets/", json={**TICKET, "supplier_id": proveedor.id})
    assert r.status_code == 201
    assert r.json()["estado"] == "abierto"


# --- Productos (base real, se deshace con rollback) ---

def test_admin_crea_y_lista_productos(session):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/products/", json={"name": "  Maiz Test  "})
    assert r.status_code == 201
    assert r.json()["name"] == "Maiz Test"
    assert "Maiz Test" in [p["name"] for p in client.get("/products/").json()]


def test_cliente_puede_listar_productos(session, producto):
    como(UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1))
    usar_sesion(session)
    r = client.get("/products/")
    assert r.status_code == 200
    assert producto.id in [p["id"] for p in r.json()]


def test_producto_duplicado_responde_409(session, producto):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/products/", json={"name": "PRODUCTO DE PRUEBA"})
    assert r.status_code == 409
    assert "Ya existe" in r.json()["detail"]


def test_ticket_con_producto_inexistente_responde_400(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/tickets/", json={**TICKET, "supplier_id": proveedor.id, "product_id": 999999})
    assert r.status_code == 400
    assert "producto" in r.json()["detail"]


def test_ticket_con_producto_existente_responde_201(session, proveedor, producto):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/tickets/", json={**TICKET, "supplier_id": proveedor.id, "product_id": producto.id})
    assert r.status_code == 201
    assert r.json()["product_id"] == producto.id


# --- Alta de clientes (base real, se deshace con rollback) ---

def test_admin_crea_cliente_y_el_cliente_puede_loguearse(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/users/", json={**CLIENTE, "supplier_id": proveedor.id})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["rol"] == "cliente"
    assert cuerpo["supplier_id"] == proveedor.id
    assert "password" not in cuerpo and "password_hash" not in cuerpo

    login = client.post("/auth/login", data={"username": CLIENTE["username"], "password": CLIENTE["password"]})
    assert login.status_code == 200


def test_usuario_duplicado_responde_409(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    datos = {**CLIENTE, "supplier_id": proveedor.id}
    assert client.post("/users/", json=datos).status_code == 201
    r = client.post("/users/", json={**datos, "username": CLIENTE["username"].upper()})
    assert r.status_code == 409


def test_cliente_con_proveedor_inexistente_responde_400(session):
    como(ADMIN)
    usar_sesion(session)
    r = client.post("/users/", json={**CLIENTE, "supplier_id": 999999})
    assert r.status_code == 400
    assert "proveedor" in r.json()["detail"]


def test_admin_modifica_clave_de_cliente_existente(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    datos = {**CLIENTE, "supplier_id": proveedor.id}
    assert client.post("/users/", json=datos).status_code == 201
    r = client.put("/users/", json={**datos, "password": "otraclave9"})
    assert r.status_code == 200
    assert "password_hash" not in r.json()

    vieja = client.post("/auth/login", data={"username": CLIENTE["username"], "password": CLIENTE["password"]})
    nueva = client.post("/auth/login", data={"username": CLIENTE["username"], "password": "otraclave9"})
    assert vieja.status_code == 401 and nueva.status_code == 200


def test_modificar_cliente_inexistente_responde_404(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.put("/users/", json={**CLIENTE, "username": "no_existe_test", "supplier_id": proveedor.id})
    assert r.status_code == 404


def test_admin_desactiva_cliente_y_queda_en_la_base(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    assert client.post("/users/", json={**CLIENTE, "supplier_id": proveedor.id}).status_code == 201

    otro_proveedor = client.delete(f"/users/{CLIENTE['username']}?supplier_id=999999")
    assert otro_proveedor.status_code == 400
    r = client.delete(f"/users/{CLIENTE['username']}?supplier_id={proveedor.id}")
    assert r.status_code == 204

    desactivado = UserRepository(session).get_user_by_username(CLIENTE["username"])
    assert desactivado is not None and desactivado.activo is False


def test_cliente_desactivado_no_entra_y_modificar_lo_reactiva(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    datos = {**CLIENTE, "supplier_id": proveedor.id}
    credenciales = {"username": CLIENTE["username"], "password": CLIENTE["password"]}
    assert client.post("/users/", json=datos).status_code == 201
    assert client.delete(f"/users/{CLIENTE['username']}?supplier_id={proveedor.id}").status_code == 204

    assert client.post("/auth/login", data=credenciales).status_code == 401
    assert client.put("/users/", json=datos).status_code == 200
    assert client.post("/auth/login", data=credenciales).status_code == 200


def test_desactivar_cliente_inexistente_responde_404(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    assert client.delete(f"/users/no_existe_test?supplier_id={proveedor.id}").status_code == 404


# --- Edición de tickets (base real, se deshace con rollback) ---

def crear_ticket_api(proveedor, **extra):
    r = client.post("/tickets/", json={**TICKET, "supplier_id": proveedor.id, **extra})
    assert r.status_code == 201
    return r.json()


def test_editar_ticket_abierto_responde_200(session, proveedor, producto):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor)
    r = client.put(f"/tickets/{ticket['id']}", json={
        "chofer": "  Juan Perez  ", "patente": "AB123CD", "peso_tara": 15000,
        "supplier_id": proveedor.id, "product_id": producto.id})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["chofer"] == "Juan Perez"
    assert (cuerpo["patente"], cuerpo["peso_tara"], cuerpo["product_id"]) == ("AB123CD", 15000, producto.id)
    assert (cuerpo["estado"], cuerpo["peso_neto"]) == ("abierto", None)


def test_editar_ticket_cerrado_recalcula_neto_en_la_base(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor, peso_bruto=48260)
    r = client.put(f"/tickets/{ticket['id']}", json={
        **TICKET, "supplier_id": proveedor.id, "peso_tara": 16000, "peso_bruto": 50000})
    assert r.status_code == 200
    assert (r.json()["estado"], r.json()["peso_neto"]) == ("cerrado", 34000)
    assert client.get(f"/tickets/{ticket['id']}").json()["peso_neto"] == 34000


def test_editar_con_bruto_menor_a_la_tara_responde_400(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor, peso_bruto=48260)
    r = client.put(f"/tickets/{ticket['id']}", json={**TICKET, "supplier_id": proveedor.id, "peso_bruto": 15160})
    assert r.status_code == 400
    assert "bruto" in r.json()["detail"]


def test_editar_ticket_inexistente_responde_404(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    r = client.put("/tickets/999999", json={**TICKET, "supplier_id": proveedor.id})
    assert r.status_code == 404


def test_editar_con_proveedor_o_producto_inexistente_responde_404(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor)
    r = client.put(f"/tickets/{ticket['id']}", json={**TICKET, "supplier_id": 999999})
    assert r.status_code == 404
    assert "proveedor" in r.json()["detail"]
    r = client.put(f"/tickets/{ticket['id']}", json={**TICKET, "supplier_id": proveedor.id, "product_id": 999999})
    assert r.status_code == 404
    assert "producto" in r.json()["detail"]


# --- Fecha del ticket (base real, se deshace con rollback) ---

def test_crear_ticket_con_fecha_vieja_responde_201(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor, fecha="2025-03-10")
    assert ticket["fecha"] == "2025-03-10"


def test_crear_ticket_sin_fecha_usa_la_de_hoy(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    assert crear_ticket_api(proveedor)["fecha"] == date.today().isoformat()


def test_crear_ticket_con_fecha_futura_responde_400(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = client.post("/tickets/", json={**TICKET, "supplier_id": proveedor.id, "fecha": manana})
    assert r.status_code == 400
    assert "fecha" in r.json()["detail"]


def test_editar_fecha_del_ticket(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    ticket = crear_ticket_api(proveedor)
    r = client.put(f"/tickets/{ticket['id']}", json={**TICKET, "supplier_id": proveedor.id, "fecha": "2025-03-10"})
    assert r.status_code == 200
    assert client.get(f"/tickets/{ticket['id']}").json()["fecha"] == "2025-03-10"



# --- Facturación (base real, se deshace con rollback) ---

def test_ticket_nuevo_se_crea_sin_facturar(session, proveedor):
    como(ADMIN)
    usar_sesion(session)
    assert crear_ticket_api(proveedor, peso_bruto=48260)["facturado"] is False
