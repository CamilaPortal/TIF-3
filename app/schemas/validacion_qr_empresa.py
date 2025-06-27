from pydantic import BaseModel, Field
from typing import Optional

class ValidarQRRequest(BaseModel):
    codigo_qr: str = Field(..., min_length=10, description="Código QR escaneado del usuario")

class ConfirmarEntregaRequest(BaseModel):
    codigo_qr: str = Field(..., min_length=10, description="Código QR a marcar como usado")

class ValidacionQRResponse(BaseModel):
    valid: bool
    message: str
    canje_info: dict
    usuario_info: dict
    empresa_info: dict
    instrucciones: list[str]

class EntregaConfirmadaResponse(BaseModel):
    success: bool
    message: str
    entrega_confirmada: dict
    qr_status: str