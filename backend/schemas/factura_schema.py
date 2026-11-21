from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

MetodoPago = Literal["Efectivo", "Transferencia", "Cheque", "E-Cheq", "Cuenta Corriente"]


def _validar_pago(modelo):
    """Pagada exige método de pago; pendiente no lo guarda."""
    if modelo.pagado and modelo.metodo_pago is None:
        raise ValueError("Si la factura está pagada, el método de pago es obligatorio")
    if not modelo.pagado:
        modelo.metodo_pago = None
    return modelo


class FacturaCreate(BaseModel):
    """Lo que el administrador envía para registrar una factura de un período."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={"example": {
            "supplier_id": 1, "numero_factura": "0001-00000142", "fecha_factura": "2026-11-20",
            "fecha_desde": "2026-11-01", "fecha_hasta": "2026-11-20", "total": 1250000.50,
            "pagado": True, "metodo_pago": "Transferencia",
        }},
    )

    supplier_id: int = Field(gt=0)
    numero_factura: str = Field(min_length=1, max_length=50)
    fecha_factura: date
    fecha_desde: date
    fecha_hasta: date
    total: float = Field(gt=0, le=9_999_999_999.99)  # entra en Numeric(12, 2)
    pagado: bool = False
    metodo_pago: Optional[MetodoPago] = None

    @model_validator(mode="after")
    def validar(self):
        if self.fecha_desde > self.fecha_hasta:
            raise ValueError("fecha_desde no puede ser posterior a fecha_hasta")
        self.total = round(self.total, 2)
        return _validar_pago(self)


class FacturaPagoUpdate(BaseModel):
    """Registrar el cobro de una factura (o volverla a pendiente)."""
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"pagado": True, "metodo_pago": "Efectivo"}})

    pagado: bool
    metodo_pago: Optional[MetodoPago] = None

    @model_validator(mode="after")
    def validar(self):
        return _validar_pago(self)


class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_factura: str
    supplier_id: int
    fecha_factura: date
    fecha_desde: date
    fecha_hasta: date
    total: float
    pagado: bool
    metodo_pago: Optional[str] = None
    cantidad_tickets: int
