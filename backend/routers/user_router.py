from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from middleware.security import exigir_admin, get_current_user
from models.user_model import UsuarioActual
from repository.supplier_repository import SupplierRepository
from repository.user_repository import UserRepository
from schemas.user_schema import ClienteCreate, UserResponse
from services.user_service import UserService
from utils.exceptions import ReglaNegocioError, UsuarioDuplicadoError, UsuarioNoEncontradoError

router = APIRouter(prefix = "/users", tags = ["Users"])


@router.post("/", response_model = UserResponse, status_code = 201)
def crear_cliente(datos: ClienteCreate, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    service = UserService(UserRepository(db), SupplierRepository(db))
    try:
        return service.crear_cliente(datos.username, datos.password, datos.supplier_id)
    except UsuarioDuplicadoError as e:
        raise HTTPException(status_code = 409, detail = str(e))
    except ReglaNegocioError as e:
        raise HTTPException(status_code = 400, detail = str(e))


@router.put("/", response_model = UserResponse)
def modificar_cliente(datos: ClienteCreate, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    """Mismo cuerpo que el alta: el cliente se busca por username y se le cambian contraseña y proveedor."""
    exigir_admin(user)
    service = UserService(UserRepository(db), SupplierRepository(db))
    try:
        return service.modificar_cliente(datos.username, datos.password, datos.supplier_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code = 404, detail = str(e))
    except ReglaNegocioError as e:
        raise HTTPException(status_code = 400, detail = str(e))


@router.delete("/{username}", status_code = 204)
def desactivar_cliente(username: str, supplier_id: int, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    """Baja lógica del cliente. Se pide el proveedor para confirmar que es el usuario correcto."""
    exigir_admin(user)
    service = UserService(UserRepository(db), SupplierRepository(db))
    try:
        service.desactivar_cliente(username, supplier_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code = 404, detail = str(e))
    except ReglaNegocioError as e:
        raise HTTPException(status_code = 400, detail = str(e))
