from datetime import date, datetime

from fastapi.testclient import TestClient

from config.database import get_db
from main import app
from middleware.security import get_current_user
from models.user_model import Rol, UsuarioActual
from services.backup_service import BackupService, nombre_de_backup

client = TestClient(app)  # sin "with": no arranca la tarea de respaldo automático

ADMIN = UsuarioActual(username="admin_test", rol=Rol.ADMIN)
CLIENTE = UsuarioActual(username="c", rol=Rol.CLIENTE, supplier_id=1)


class RepositorioFalso:
    """Devuelve filas fijas por tabla, sin base de datos."""
    def __init__(self):
        self.filas = {
            "suppliers": [{"id": 1, "name": r"O'Brien \ Hnos", "cuit": None, "phone": None,
                           "fecha_alta": date(2026, 11, 1)}],
            "products": [],
            "users": [],
            "facturas": [],
            "tickets": [{"id": 7, "fecha": date(2026, 11, 20), "chofer": "Ivan", "transporte": "Equipo",
                         "patente": None, "supplier_id": 1, "product_id": None, "peso_tara": 15160,
                         "peso_bruto": None, "peso_neto": None, "estado": "abierto", "numero_ticket": None}],
        }

    def leer_tabla(self, tabla):
        return self.filas[tabla.name]


def teardown_function():
    app.dependency_overrides.clear()


# --- Servicio ---

def test_nombre_de_backup_lleva_la_fecha():
    assert nombre_de_backup(date(2026, 11, 20)) == "agropeso_backup_2026-11-20.sql"


def test_sql_tiene_metadatos_y_un_insert_por_fila():
    sql = BackupService(RepositorioFalso()).generar_sql(datetime(2026, 11, 20, 18, 30))
    assert "-- fecha_generacion: 2026-11-20T18:30:00" in sql
    assert "-- total_proveedores: 1" in sql
    assert "-- total_tickets: 1" in sql
    assert sql.count("INSERT INTO") == 2
    # Proveedores antes que tickets (clave foránea)
    assert sql.index("INSERT INTO suppliers") < sql.index("INSERT INTO tickets")


def test_sql_escapa_textos_y_escribe_null_y_fechas():
    sql = BackupService(RepositorioFalso()).generar_sql()
    assert r"'O''Brien \\ Hnos'" in sql  # comilla duplicada y barra escapada
    assert "'2026-11-01'" in sql
    assert "NULL" in sql


def test_guardar_backup_del_dia_solo_una_vez(tmp_path):
    service = BackupService(RepositorioFalso())
    archivo = service.guardar_backup_del_dia(tmp_path, date(2026, 11, 20))
    assert archivo == tmp_path / "agropeso_backup_2026-11-20.sql"
    assert "INSERT INTO tickets" in archivo.read_text(encoding="utf-8")
    assert service.guardar_backup_del_dia(tmp_path, date(2026, 11, 20)) is None
    assert [a.name for a in tmp_path.iterdir()] == ["agropeso_backup_2026-11-20.sql"]


# --- Endpoint ---

def test_backup_sin_token_responde_401():
    assert client.get("/backup/descargar").status_code == 401


def test_cliente_no_puede_descargar_backup():
    app.dependency_overrides[get_current_user] = lambda: CLIENTE
    assert client.get("/backup/descargar").status_code == 403


def test_admin_descarga_backup_con_todos_los_datos(session, proveedor, producto):
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    app.dependency_overrides[get_db] = lambda: session

    r = client.get("/backup/descargar")

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/octet-stream"
    assert r.headers["content-disposition"] == \
        f'attachment; filename="agropeso_backup_{date.today().isoformat()}.sql"'
    assert "'Proveedor de prueba'" in r.text
    assert "'Producto de prueba'" in r.text
