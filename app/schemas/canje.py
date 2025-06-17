from pydantic import BaseModel, Field

class CanjeCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100, example="Taza Ecológica")
    descripcion: str = Field(..., max_length=255, example="Taza hecha con materiales reciclados.")
    puntos: int = Field(..., gt=0, example=100)

class CanjeUpdateRequest(BaseModel):
    puntos: int = Field(..., gt=0, example=120, description="El nuevo valor de puntos para el ítem de canje.")

class CanjeUpdateEstadoRequest(BaseModel):
    is_active: bool = Field(..., description="Define si el ítem de canje está activo (true) o inactivo (false).")

class CanjeItemResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str
    puntos: int

    class Config:
        orm_mode = True