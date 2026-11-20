from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.database import get_db
from middleware.security import exigir_admin, get_current_user
from models.products import ProductEntity
from models.user_model import UsuarioActual
from repository.product_repository import ProductRepository
from schemas.product_schema import ProductCreate, ProductResponse
from services.product_service import ProductService
from utils.exceptions import ProductoDuplicadoError

router = APIRouter(prefix = "/products", tags = ["Products"])


@router.get("/", response_model = list[ProductResponse])
def listar_productos(db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    service = ProductService(ProductRepository(db))
    return service.obtener_todos_los_productos()


@router.post("/", response_model = ProductResponse, status_code = 201)
def crear_producto(datos: ProductCreate, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    service = ProductService(ProductRepository(db))
    producto = ProductEntity(**datos.model_dump())  # esquema -> entidad pura
    try:
        return service.crear_producto(producto)
    except ProductoDuplicadoError as e:
        raise HTTPException(status_code = 409, detail = str(e))
