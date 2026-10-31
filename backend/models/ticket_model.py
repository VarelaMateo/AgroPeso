from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import relationship

from config.database import Base


@dataclass
class Ticket:  # Entidad pura
    fecha: date
    chofer: str
    patente: Optional[str]
    peso_tara: int
    peso_bruto: int
    supplier_id: int
    product_id: Optional[int] = None
    transporte: str = "Equipo"
    numero_ticket: Optional[int] = None

    @property
    def peso_neto(self) -> int:
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
    peso_bruto = Column(Integer, nullable=False)
    peso_neto = Column(Integer, nullable=False)
    numero_ticket = Column(Integer, nullable=True, unique=True)

    supplier = relationship("Supplier", back_populates="tickets")
    product = relationship("Product", back_populates="tickets")