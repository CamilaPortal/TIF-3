from pydantic import BaseModel

class CanjeRequest(BaseModel):
    cesto_id: str
    cantidad_botellas: int
    peso: float
