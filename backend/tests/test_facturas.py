from fastapi.testclient import TestClient

from config.database import get_db
from main import app
from middleware.security import get_current_user
from models.user_model import Rol, UsuarioActual

client = TestClient(app)

ADMIN = UsuarioActual(username="admin_test", rol=Rol.ADMIN)
CLIENTE = UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1)
FACTURA = {"numero_factura": "TEST-0001", "fecha_factura": "2025-04-05", "fecha_desde": "2025-03-01",
           "fecha_hasta": "2025-03-31", "total": 1250000.5, "pagado": False}


def como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


def admin_con_base(session):
    como(ADMIN)
    app.dependency_overrides[get_db] = lambda: session


def teardown_function():
    app.dependency_overrides.clear()


def pesada(proveedor, fecha, bruto=48260):
    datos = {"chofer": "Ivan", "peso_tara": 15160, "supplier_id": proveedor.id, "fecha": fecha}
    if bruto is not None:
        datos["peso_bruto"] = bruto
    r = client.post("/tickets/", json=datos)
    assert r.status_code == 201
    return r.json()["id"]


def ticket(ticket_id):
    return client.get(f"/tickets/{ticket_id}").json()


# --- Seguridad y validación (sin base) ---

def test_sin_token_responde_401():
    assert client.get("/facturas/").status_code == 401
    assert client.post("/facturas/", json={**FACTURA, "supplier_id": 1}).status_code == 401


def test_cliente_recibe_403_en_todos_los_endpoints():
    como(CLIENTE)
    assert client.get("/facturas/").status_code == 403
    assert client.post("/facturas/", json={**FACTURA, "supplier_id": 1}).status_code == 403
    assert client.patch("/facturas/1/pago", json={"pagado": True, "metodo_pago": "Efectivo"}).status_code == 403
    assert client.delete("/facturas/1").status_code == 403


def test_validaciones_de_entrada_responden_422():
    como(ADMIN)
    base = {**FACTURA, "supplier_id": 1}
    for invalido in [
        {"fecha_desde": "2025-04-01"},                      # desde posterior a hasta
        {"total": 0},                                      # total no positivo
        {"pagado": True},                                  # pagada sin método
        {"pagado": True, "metodo_pago": "Bitcoin"},        # método inválido
        {"facturado": True},                               # campo extra
    ]:
        assert client.post("/facturas/", json={**base, **invalido}).status_code == 422, invalido
    assert client.patch("/facturas/1/pago", json={"pagado": True}).status_code == 422


# --- Con base real (se deshace con rollback) ---

def test_crear_factura_incluye_solo_cerradas_sin_facturar_del_periodo(session, proveedor):
    admin_con_base(session)
    dentro_1 = pesada(proveedor, "2025-03-01")
    dentro_2 = pesada(proveedor, "2025-03-31")
    abierta = pesada(proveedor, "2025-03-15", bruto=None)
    fuera = pesada(proveedor, "2025-04-01")

    r = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id,
                                         "pagado": True, "metodo_pago": "Transferencia"})

    assert r.status_code == 201
    factura = r.json()
    assert (factura["cantidad_tickets"], factura["total"], factura["metodo_pago"]) == (2, 1250000.5, "Transferencia")
    for t in (dentro_1, dentro_2):
        assert (ticket(t)["facturado"], ticket(t)["factura_id"]) == (True, factura["id"])
    for t in (abierta, fuera):
        assert (ticket(t)["facturado"], ticket(t)["factura_id"]) == (False, None)


def test_factura_pendiente_no_guarda_metodo(session, proveedor):
    admin_con_base(session)
    pesada(proveedor, "2025-03-10")
    r = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id, "metodo_pago": "Cheque"})
    assert (r.json()["pagado"], r.json()["metodo_pago"]) == (False, None)


def test_numero_duplicado_responde_409(session, proveedor):
    admin_con_base(session)
    pesada(proveedor, "2025-03-10")
    pesada(proveedor, "2025-05-10")
    assert client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id}).status_code == 201
    r = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id,
                                         "fecha_desde": "2025-05-01", "fecha_hasta": "2025-05-31"})
    assert r.status_code == 409


def test_sin_pesadas_para_facturar_responde_400_y_no_guarda(session, proveedor):
    admin_con_base(session)
    pesada(proveedor, "2025-03-10", bruto=None)  # abierta: no cuenta
    r = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id})
    assert r.status_code == 400
    assert "No hay pesadas" in r.json()["detail"]
    assert client.get(f"/facturas/?supplier_id={proveedor.id}").json() == []


def test_proveedor_inexistente_responde_404(session):
    admin_con_base(session)
    assert client.post("/facturas/", json={**FACTURA, "supplier_id": 999999}).status_code == 404


def test_registrar_pago_de_factura_pendiente(session, proveedor):
    admin_con_base(session)
    pesada(proveedor, "2025-03-10")
    factura = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id}).json()

    r = client.patch(f"/facturas/{factura['id']}/pago", json={"pagado": True, "metodo_pago": "E-Cheq"})

    assert r.status_code == 200
    assert (r.json()["pagado"], r.json()["metodo_pago"], r.json()["cantidad_tickets"]) == (True, "E-Cheq", 1)
    assert client.patch("/facturas/999999/pago", json={"pagado": True, "metodo_pago": "Efectivo"}).status_code == 404


def test_listar_filtra_por_proveedor(session, proveedor):
    admin_con_base(session)
    pesada(proveedor, "2025-03-10")
    factura = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id}).json()
    assert [f["id"] for f in client.get(f"/facturas/?supplier_id={proveedor.id}").json()] == [factura["id"]]
    assert factura["id"] in [f["id"] for f in client.get("/facturas/").json()]


def test_anular_factura_libera_sus_pesadas(session, proveedor):
    admin_con_base(session)
    t = pesada(proveedor, "2025-03-10")
    factura = client.post("/facturas/", json={**FACTURA, "supplier_id": proveedor.id}).json()

    assert client.delete(f"/facturas/{factura['id']}").status_code == 204

    assert (ticket(t)["facturado"], ticket(t)["factura_id"]) == (False, None)
    assert client.get(f"/facturas/?supplier_id={proveedor.id}").json() == []
    assert client.delete(f"/facturas/{factura['id']}").status_code == 404
