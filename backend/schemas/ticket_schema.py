from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

"""
Field(gt=0): el número tiene que ser mayor que 0.

Field(min_length=1): el texto no puede ser vacío.

max_length: usé los mismos largos que tus columnas de MySQL (String(200), String(11), String(50)). 
Así, un texto demasiado largo se rechaza en la API con un error claro, y no explota después en la base.

= None o default=...: el campo es opcional, igual que en tu entidad.

Optional[...] indica que el valor puede ser None. """

class TicketBase(BaseModel): 
    """Campos comunes a lo que entra y a lo que sale."""
    model_config = ConfigDict(str_strip_whitespace=True)

    chofer: str = Field(min_length=1, max_length=200)
    patente: Optional[str] = Field(default=None, max_length=11)
    peso_tara: int = Field(gt=0)
    peso_bruto: int = Field(gt=0)
    supplier_id: int = Field(gt=0)
    product_id: Optional[int] = Field(default=None, gt=0)
    transporte: str = Field(default="Equipo", max_length=50)
    numero_ticket: Optional[int] = None

class TicketCreate(TicketBase):
    """Lo que el cliente envía para registrar una pesada."""
    model_config = ConfigDict(
        extra="forbid", #Si alguien manda "id": 99 o "peso_neto": 5 en el JSON, on extra="forbid", la API responde un error 422 que dice cuál es el campo sobrante.
        json_schema_extra={
            "example": {
                "chofer": "Ivan Derio",
                "patente": "HKN279",
                "peso_tara": 15160,
                "peso_bruto": 48260,
                "supplier_id": 1,
            }
        },
    )

    fecha: date = Field(default_factory=date.today)

class TicketResponse(TicketBase):
    """Lo que la API devuelve."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    peso_neto: int