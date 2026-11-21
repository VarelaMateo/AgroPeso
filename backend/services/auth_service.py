import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext
from models.user_model import User

load_dotenv()

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
LARGO_MAXIMO_CLAVE = 128  # más largo que esto no es una contraseña real: se rechaza sin hashear

# Se verifica contra este hash cuando el usuario no existe, para que la respuesta tarde lo mismo
# y no se pueda averiguar qué usuarios existen midiendo el tiempo.
_HASH_DE_RELLENO = pwd_context.hash("relleno-para-igualar-tiempos")

if 0 < len(os.getenv("SECRET_KEY", "")) < 32:
    logging.getLogger("agropeso.seguridad").warning(
        "SECRET_KEY es corta (menos de 32 caracteres): generá una con "
        "python -c \"import secrets; print(secrets.token_hex(32))\"")

def _secret_key() -> str:
    clave = os.getenv("SECRET_KEY")
    if not clave:
        raise RuntimeError("Falta SECRET_KEY en el archivo")
    return clave

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta]= None)-> str:
    minutos = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    vencimiento = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=minutos))
    payload = {**data, "exp":vencimiento}

    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)

def authenticate_user(repo, username: str, password:str) -> Optional[User]:
    if len(password) > LARGO_MAXIMO_CLAVE:
        return None
    user = repo.get_user_by_username(username)
    if user is None:
        verify_password(password, _HASH_DE_RELLENO)
        return None
    return user if verify_password(password, user.password_hash) else None

def decode_access_token(token: str) -> dict:
    #verifica la firma y el vencimiento. Lanza jwt.PyJWTError si el token no es valido
    return jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
