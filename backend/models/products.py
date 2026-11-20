from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from config.database import Base


@dataclass
class ProductEntity:  # Entidad pura
    name: str
    id: Optional[int] = None


class Product(Base):  # Tabla de MySQL
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)

    tickets = relationship("TicketDB", back_populates="product")
