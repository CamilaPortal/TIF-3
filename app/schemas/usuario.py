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
