from sqlalchemy import Column, Integer, String, Date, func
from sqlalchemy.orm import relationship

from config.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    cuit = Column(String(11), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    fecha_alta = Column(Date, server_default=func.curdate(), nullable=False)

    pesadas = relationship("Pesada", back_populates="supplier")