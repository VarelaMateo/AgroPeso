from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    #"Lo que el cliente envia para crear un producto"
    model_config = ConfigDict(
        str_strip_whitespace = True,
        extra = "forbid",
        json_schema_extra = {"example": {"name": "Soja"}},
    )

    name: str = Field(min_length = 1, max_length = 200)


class ProductResponse(BaseModel):
    #"Lo que la API devuelve"
    model_config = ConfigDict(from_attributes = True)

    id: int
    name: str
