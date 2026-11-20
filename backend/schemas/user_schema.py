from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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


class ClienteCreate(BaseModel):
    """Lo que el admin envía para dar de alta un cliente. El rol lo fija el servidor."""
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"username": "berg", "password": "clave123", "supplier_id": 1}},
    )

    username: str = Field(min_length=3, max_length=50)
    # La contraseña no se recorta: un espacio al final es parte de la clave
    password: str = Field(min_length=6)
    supplier_id: int = Field(gt=0)

    @field_validator("username")
    @classmethod
    def limpiar_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El usuario debe tener al menos 3 caracteres")
        return v

    @field_validator("password")
    @classmethod
    def limite_de_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("La contraseña puede tener hasta 72 bytes (límite de bcrypt)")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: Rol
    supplier_id: Optional[int] = None
    