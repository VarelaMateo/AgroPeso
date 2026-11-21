from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from config.database import get_db
from middleware.security import exigir_admin, get_current_user
from models.factura_model import Factura
from models.user_model import UsuarioActual
from repository.factura_repository import FacturaRepository
from repository.supplier_repository import SupplierRepository
from schemas.factura_schema import FacturaCreate, FacturaPagoUpdate, FacturaResponse
from services.factura_service import FacturaService
from utils.exceptions import FacturaDuplicadaError, ReferenciaNoEncontradaError, ReglaNegocioError

router = APIRouter(prefix="/facturas", tags=["Facturas"])


def crear_servicio(db: Session) -> FacturaService:
    return FacturaService(FacturaRepository(db), SupplierRepository(db))


@router.post("/", response_model=FacturaResponse, status_code=201)
def crear_factura(datos: FacturaCreate, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    try:
        return crear_servicio(db).crear_factura(Factura(**datos.model_dump()))
    except ReferenciaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FacturaDuplicadaError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ReglaNegocioError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[FacturaResponse])
def listar_facturas(supplier_id: Optional[int] = None, db: Session = Depends(get_db),
                    user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    return crear_servicio(db).obtener_facturas(supplier_id)


@router.patch("/{factura_id}/pago", response_model=FacturaResponse)
def registrar_pago(factura_id: int, datos: FacturaPagoUpdate, db: Session = Depends(get_db),
                   user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    try:
        return crear_servicio(db).registrar_pago(factura_id, datos.pagado, datos.metodo_pago)
    except ReferenciaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{factura_id}", status_code=204)
def anular_factura(factura_id: int, db: Session = Depends(get_db), user: UsuarioActual = Depends(get_current_user)):
    exigir_admin(user)
    try:
        crear_servicio(db).anular_factura(factura_id)
    except ReferenciaNoEncontradaError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(status_code=204)
