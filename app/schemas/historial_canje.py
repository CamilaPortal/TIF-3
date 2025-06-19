from pydantic import BaseModel, Field
from datetime import datetime 


class RealizarCanjeRequest(BaseModel):
    canje_id: int = Field(..., description="ID del premio a canjear")

class HistorialCanjeResponse(BaseModel):
    id: int
    puntos_usados: int
    fecha_canje: datetime
    usuario_dni: int
    canje_id: int

    class Config:
        orm_mode = True

class HistorialCanjeDetalladoResponse(BaseModel):
    """Schema detallado para el historial con información del canje"""
    id: int
    puntos_usados: int
    fecha_canje: datetime
    usuario_dni: int
    canje_id: int
    # Detalles del canje
    canje_nombre: str
    canje_descripcion: str

    class Config:
        orm_mode = True