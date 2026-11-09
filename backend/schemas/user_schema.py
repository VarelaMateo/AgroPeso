from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from models.user_model import Rol

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    rol: Rol
    supplier_id: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validar_rol_y_proveedor(self):
        if self.rol == Rol.CLIENTE and self.supplier_id is None:
            raise ValueError("Un usuario con el rol 'cliente' debe tener supplier_id")
        if self.rol == Rol.ADMIN and self.supplier_id is not None:
            raise ValueError("Un usuario con rol 'admin' no puede tener supplier_id")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: Rol
    supplier_id: Optional[int] = None
    