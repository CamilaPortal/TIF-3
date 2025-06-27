from pydantic import BaseModel, EmailStr, Field
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