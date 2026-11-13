from dataclasses import dataclass
from enum import Enum
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from config.database import Base

class Rol(str, Enum):
    ADMIN = "admin"
    CLIENTE = "cliente"

@dataclass
class User:
    #Entidad pura de dominio
    username: str
    password_hash: str
    rol: Rol
    supplier_id: Optional[int] = None
    id: Optional[int] = None


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key= True, autoincrement=True)
    username = Column(String(50), unique= True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(10), nullable= False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable= True)

    supplier = relationship("Supplier")

@dataclass
class UsuarioActual:
    username: str
    rol: Rol
    supplier_id: Optional[int] = None
    