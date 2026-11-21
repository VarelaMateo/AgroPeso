from getpass import getpass

from config.database import SessionLocal
from models.user_model import Rol, User
from repository.user_repository import UserRepository
from services.auth_service import get_password_hash

username = input("Usuario: ").strip()
password = getpass("Contraseña (mínimo 8 caracteres): ")

if not 3 <= len(username) <= 50:
    raise SystemExit("El usuario debe tener entre 3 y 50 caracteres")
if len(password) < 8:
    raise SystemExit("La contraseña debe tener al menos 8 caracteres")
if len(password.encode("utf-8")) > 72:
    raise SystemExit("La contraseña puede tener hasta 72 bytes (límite de bcrypt)")
if password.strip().lower() == username.lower():
    raise SystemExit("La contraseña no puede ser igual al usuario")
if getpass("Repetir contraseña: ") != password:
    raise SystemExit("Las contraseñas no coinciden")

session = SessionLocal()
try:
    repo = UserRepository(session)
    repo.create_user(User(username=username, password_hash=get_password_hash(password), rol=Rol.ADMIN))
    print("Usuario admin creado.")
finally:
    session.close()
