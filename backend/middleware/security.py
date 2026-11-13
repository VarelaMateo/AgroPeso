import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from models.user_model import Rol, UsuarioActual
from services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/login")

def  get_current_user(token: str = Depends(oauth2_scheme)) -> UsuarioActual:
    try:
        datos = decode_access_token(token)
        return UsuarioActual(
            username = datos["username"],
            rol = Rol(datos["rol"]),
            supplier_id = datos.get("supplier_id")
        )
    except (jwt.PyJWKError, KeyError, ValueError):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token invalido o vencido",
            headers = {"WWW-Authenticate": "Bearer"}
        ) from None

def exigir_admin(user: UsuarioActual) -> None:
    if user.rol != Rol.ADMIN:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "No tienes permisos para esta accion",
        )   

