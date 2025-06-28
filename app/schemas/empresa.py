from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class EmpresaCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    direccion: str = Field(..., max_length=200)
    telefono: int
    email: EmailStr

class EmpresaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    direccion: str
    telefono: str
    email: str
    is_active: bool

    class Config:
        orm_mode = True

class EmpresaUsuarioCreateRequest(BaseModel):
    """Schema para crear un usuario de empresa"""
    dni: int
    alias: str
    nombre: str
    apellido: str
    telefono: int
    email: EmailStr
    password: Optional[str] = None
    empresa_id: int


class CambiarPasswordRequest(BaseModel):
    password_actual: str = Field(..., min_length=1, description="Contraseña actual")
    password_nueva: str = Field(..., min_length=6, description="Nueva contraseña (mínimo 6 caracteres)")
    confirmar_password: str = Field(..., min_length=6, description="Confirmación de la nueva contraseña")

    @validator('confirmar_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password_nueva' in values and v != values['password_nueva']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class CambiarPasswordResponse(BaseModel):
    message: str
    timestamp: str