import threading
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.database import get_db
from repository.user_repository import UserRepository
from services.auth_service import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# Freno a la fuerza bruta: después de MAX_FALLIDOS errores para un usuario en VENTANA_SEGUNDOS, se bloquea
# ese usuario hasta que pase la ventana (aunque la contraseña sea correcta).
# shortcut: en memoria y por proceso; si la API corre con varias réplicas o workers, pasarlo a la base o a Redis.
MAX_FALLIDOS = 5
VENTANA_SEGUNDOS = 15 * 60
_fallidos: dict[str, list[float]] = {}
_candado = threading.Lock()


def _fallos_recientes(clave: str) -> list[float]:
    limite = time.monotonic() - VENTANA_SEGUNDOS
    recientes = [t for t in _fallidos.get(clave, []) if t > limite]
    _fallidos[clave] = recientes
    return recientes

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    clave = form.username.strip().lower()
    with _candado:
        fallos = _fallos_recientes(clave)
        if len(fallos) >= MAX_FALLIDOS:
            espera = int(fallos[0] + VENTANA_SEGUNDOS - time.monotonic()) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos fallidos. Probá de nuevo en {espera // 60 + 1} minutos",
                headers={"Retry-After": str(espera)},
            )

    user = authenticate_user(UserRepository(db), form.username, form.password)
    if user is None:
        with _candado:
            _fallos_recientes(clave).append(time.monotonic())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasenia incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    with _candado:
        _fallidos.pop(clave, None)

    token = create_access_token(
        {"username": user.username,
         "rol": user.rol.value,
         "supplier_id": user.supplier_id}
    )

    return {"access_token": token, "token_type": "bearer"}