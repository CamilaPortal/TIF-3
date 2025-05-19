from pydantic import BaseModel

class QrTokenGenerate(BaseModel):
    cesto_id: str
    cantidad_botellas: int
    peso: float
    is_used: bool = False
