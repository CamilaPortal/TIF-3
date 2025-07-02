from pydantic import BaseModel, Field

class CanjeCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100, example="Taza Ecológica")
    descripcion: str = Field(..., max_length=255, example="Taza hecha con materiales reciclados.")
    puntos: int = Field(..., gt=0, example=100)
    stock_inicial: int = Field(..., ge=1, example=50, description="Cantidad inicial de stock (obligatorio)")

class CanjeUpdateRequest(BaseModel):
    puntos: int = Field(..., gt=0, example=120, description="El nuevo valor de puntos para el ítem de canje.")

class CanjeUpdateStockRequest(BaseModel):
    """Schema para actualizar stock de un canje"""
    nuevo_stock: int = Field(..., ge=0, description="Nueva cantidad de stock (reemplaza el actual)")

class CanjeUpdateEstadoRequest(BaseModel):
    is_active: bool = Field(..., description="Define si el ítem de canje está activo (true) o inactivo (false).")

class CanjeItemResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str
    puntos: int
    empresa_id: int
    empresa_nombre: str 
    is_active: bool
    stock_inicial: int
    stock_actual: int

    class Config:
        orm_mode = True

class CanjeItemDetalladoResponse(BaseModel):
    """Response con información completa de la empresa"""
    id: int
    nombre: str
    descripcion: str
    puntos: int
    empresa_id: int
    empresa_nombre: str
    empresa_direccion: str
    empresa_telefono: str
    stock_actual: int

    class Config:
        orm_mode = True