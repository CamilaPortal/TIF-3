from fastapi import APIRouter, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioLogin, UsuarioRegister, TokenResponse


auth = APIRouter()

@auth.post('/register')
def register(
    data: UsuarioRegister,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    usuario_existente = db.query(Usuario).filter(Usuario.email == data.email).first()
    if usuario_existente:
        raise HTTPException(status_code=409, detail="Correo ya registrado")

    usuario_por_alias = db.query(Usuario).filter(Usuario.alias == data.alias).first()
    if usuario_por_alias:
        raise HTTPException(status_code=409, detail="Alias ya registrado. Por favor, elige otro.")

    nuevo_usuario = Usuario(
        dni=data.dni,
        alias=data.alias,
        nombre=data.nombre,
        apellido=data.apellido,
        telefono=data.telefono,
        email=data.email,
        rol=data.rol or "user"
    )
    nuevo_usuario.set_password(data.password)

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {
        "message": "Usuario registrado exitosamente"
    }


@auth.post('/login', response_model=TokenResponse)
def login(
    data: UsuarioLogin,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    usuario = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not usuario or not usuario.check_password(data.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = Authorize.create_access_token(
        subject=str(usuario.dni),
        user_claims={
            "email": usuario.email,
            "rol": usuario.rol
        }
    )

    return {
        "access_token": access_token,
        "dni": usuario.dni,
        "email": usuario.email,
        "rol": usuario.rol
    }
