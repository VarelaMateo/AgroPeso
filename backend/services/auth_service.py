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
    user = repo.get_user_by_username(username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user

