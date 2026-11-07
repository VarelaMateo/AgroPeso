from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import relationship

from config.database import Base

class EstadoTicket(str, Enum):
    ABIERTO = "abierto"
    CERRADO = "cerrado"

@dataclass
class Ticket:  # Entidad pura
    fecha: date
    chofer: str
    patente: Optional[str]
    peso_tara: int
    peso_bruto: Optional[int]
    supplier_id: int
    product_id: Optional[int] = None
    transporte: str = "Equipo"
    numero_ticket: Optional[int] = None
    estado: EstadoTicket = EstadoTicket.ABIERTO
    id: Optional[int] = None

    @property
    def peso_neto(self) -> Optional[int]:
        if self.peso_bruto is None:
            return None
        return self.peso_bruto - self.peso_tara


class TicketDB(Base):  # Tabla de MySQL
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, server_default=func.curdate(), nullable=False)

    chofer = Column(String(200), nullable=False)
    transporte = Column(String(50), default="Equipo")
    patente = Column(String(11), nullable=True)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    peso_tara = Column(Integer, nullable=False)
    peso_bruto = Column(Integer, nullable=True)
    peso_neto = Column(Integer, nullable=True)
    estado = Column(String(10), nullable=False, default="abierto", server_default="abierto")
    numero_ticket = Column(Integer, nullable=True, unique=True)

    supplier = relationship("Supplier", back_populates="tickets")
    product = relationship("Product", back_populates="tickets")