from typing import Optional

from models.factura_model import Factura
from repository.factura_repository import FacturaRepository
from repository.supplier_repository import SupplierRepository
from utils.exceptions import FacturaDuplicadaError, ReferenciaNoEncontradaError, ReglaNegocioError


class FacturaService:
    def __init__(self, repository: FacturaRepository, supplier_repository: SupplierRepository):
        self.repository = repository
        self.supplier_repository = supplier_repository

    def crear_factura(self, factura: Factura) -> Factura:
        if self.supplier_repository.get_supplier_by_id(factura.supplier_id) is None:
            raise ReferenciaNoEncontradaError(f"No existe el proveedor con id {factura.supplier_id}")
        if self.repository.get_factura_by_numero(factura.numero_factura) is not None:
            raise FacturaDuplicadaError(f"Ya existe la factura '{factura.numero_factura}'")

        creada = self.repository.crear_factura(factura)
        if creada is None:
            raise ReglaNegocioError(
                f"No hay pesadas cerradas sin facturar de ese proveedor entre el "
                f"{factura.fecha_desde.strftime('%d/%m/%Y')} y el {factura.fecha_hasta.strftime('%d/%m/%Y')}")
        return creada

    def obtener_facturas(self, supplier_id: Optional[int] = None) -> list[Factura]:
        return self.repository.get_all_facturas(supplier_id)

    def registrar_pago(self, factura_id: int, pagado: bool, metodo_pago: Optional[str]) -> Factura:
        actualizada = self.repository.actualizar_pago(factura_id, pagado, metodo_pago)
        if actualizada is None:
            raise ReferenciaNoEncontradaError(f"No existe la factura con id {factura_id}")
        return actualizada

    def anular_factura(self, factura_id: int) -> None:
        if not self.repository.anular_factura(factura_id):
            raise ReferenciaNoEncontradaError(f"No existe la factura con id {factura_id}")
