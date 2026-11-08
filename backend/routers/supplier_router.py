from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.suppliers import SupplierEntity
from repository.supplier_repository import SupplierRepository
from schemas.supplier_schema import SupplierCreate, SupplierResponse
from services.supplier_service import SupplierService

router = APIRouter(prefix = "/suppliers", tags=["Suppliers"])

@router.get("/", response_model = list[SupplierResponse])
def listar_proveedores(db: Session = Depends(get_db)):
    service = SupplierService(SupplierRepository(db))
    return service.obtener_todos_los_proveedores()

@router.post("/",  response_model = SupplierResponse, status_code = 200)
def crear_proveedor(datos: SupplierCreate, db: Session = Depends(get_db)):
    service = SupplierService(SupplierRepository(db))
    proveedor = SupplierEntity(**datos.model_dump()) #esquema -> entidad pura
    return service.crear_proveedor(proveedor)


