from pydantic import BaseModel, EmailStr

class UsuarioRegister(BaseModel):
    dni: int
    alias: str
    nombre: str
    apellido: str
    telefono: int
    email: EmailStr
    password: str
    rol: str = "user"

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class UsuarioResponse(BaseModel):
    dni: int
    alias: str
    nombre: str
    apellido: str
    telefono: int
    email: EmailStr
    puntos_disponibles: int

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    dni: int
    email: EmailStr
    rol: str

class UsuarioRankingResponse(BaseModel):
    """Schema para mostrar usuarios en el ranking"""
    posicion: int
    alias: str
    nombre: str
    apellido: str
    puntos_disponibles: int
    total_puntos_ganados: int
    total_reciclajes_realizados: int

    class Config:
        orm_mode = True