from getpass import getpass

from config.database import SessionLocal
from models.user_model import Rol, User
from repository.user_repository import UserRepository
from services.auth_service import get_password_hash

username = input("Usuario: ").strip()
password = getpass("Contraseña: ")

session = SessionLocal()
try:
    repo = UserRepository(session)
    repo.create_user(User(username=username, password_hash=get_password_hash(password), rol=Rol.ADMIN))
    print("Usuario admin creado.")
finally:
    session.close()