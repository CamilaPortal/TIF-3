from pydantic import BaseModel

class ReciclajeRequest(BaseModel):
    cesto_id: str
    cantidad_botellas: int
    peso: float
