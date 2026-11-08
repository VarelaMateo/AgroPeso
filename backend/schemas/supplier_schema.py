from pydantic import BaseModel, ConfigDict, Field

class SupplierCreate (BaseModel):
    #"Lo que el cliente envia para crear un proveedor"
    model_config = ConfigDict(
        str_strip_whitespace = True,
        extra = "forbid",
        json_schema_extra = {"example": {"name": "berg"}},
    )

    name: str = Field(min_length = 1, max_length = 200)

class SupplierResponse(BaseModel):
    #"Lo que la API devuelve"
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str