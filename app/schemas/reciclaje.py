from pydantic import BaseModel, Field
from datetime import datetime

class ReciclajeConfirmQR(BaseModel):
    qr_token_value: str = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef")

class ReciclajeResponse(BaseModel):
    id: int
    puntos: int
    usuario_dni: int
    qr_token_id: int

    class Config:
        orm_mode = True


class ReciclajeHistorialResponse(BaseModel):
    id: int
    puntos: int
    fecha_reciclaje: datetime
    peso: int
    cantidad_botellas: int
    id_cesto: str
    
    class Config:
        orm_mode = True