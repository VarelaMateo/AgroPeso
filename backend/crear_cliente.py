from getpass import getpass

from config.database import SessionLocal
from models.user_model import Rol, User
from repository.supplier_repository import SupplierRepository
from repository.user_repository import UserRepository
from services.auth_service import get_password_hash

session = SessionLocal()
try:
    proveedores = SupplierRepository(session).get_all_suppliers()
    if not proveedores:
        print("No hay proveedores cargados. Creá uno primero desde el panel de admin.")
        raise SystemExit(1)

    print("Proveedores disponibles:")
    for p in proveedores:
        print(f"  {p.id}: {p.name}")

    ids_validos = {p.id for p in proveedores}
    entrada = input("ID del proveedor del cliente: ").strip()
    if not entrada.isdigit() or int(entrada) not in ids_validos:
        print("ID de proveedor inválido.")
        raise SystemExit(1)
    supplier_id = int(entrada)

    username = input("Usuario: ").strip()
    if not username or len(username) > 50:
        print("El usuario es obligatorio y puede tener hasta 50 caracteres.")
        raise SystemExit(1)

    repo = UserRepository(session)
    if repo.get_user_by_username(username):
        print(f"Ya existe el usuario '{username}'.")
        raise SystemExit(1)

    password = getpass("Contraseña: ")
    if not password or len(password.encode("utf-8")) > 72:
        print("La contraseña es obligatoria y puede tener hasta 72 bytes (límite de bcrypt).")
        raise SystemExit(1)
    if password != getpass("Repetir contraseña: "):
        print("Las contraseñas no coinciden.")
        raise SystemExit(1)

    repo.create_user(User(
        username=username,
        password_hash=get_password_hash(password),
        rol=Rol.CLIENTE,
        supplier_id=supplier_id,
    ))
    print(f"Cliente '{username}' creado y asociado al proveedor {supplier_id}.")
finally:
    session.close()