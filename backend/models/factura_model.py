from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String

from config.database import Base

METODOS_DE_PAGO = ("Efectivo", "Transferencia", "Cheque", "E-Cheq", "Cuenta Corriente")


@dataclass
class Factura:  # Entidad pura
    numero_factura: str
    supplier_id: int
    fecha_factura: date
    fecha_desde: date
    fecha_hasta: date
    total: float
    pagado: bool = False
    metodo_pago: Optional[str] = None
    id: Optional[int] = None
    cantidad_tickets: int = 0  # pesadas incluidas (se calcula, no es una columna)


class FacturaDB(Base):  # Tabla de MySQL
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_factura = Column(String(50), nullable=False, unique=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    fecha_factura = Column(Date, nullable=False)
    fecha_desde = Column(Date, nullable=False)
    fecha_hasta = Column(Date, nullable=False)
    total = Column(Numeric(12, 2, asdecimal=False), nullable=False)  # asdecimal=False: llega como float
    pagado = Column(Boolean, nullable=False, default=False, server_default="0")
    metodo_pago = Column(String(50), nullable=True)
