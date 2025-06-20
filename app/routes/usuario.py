from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT

from app.db.connection import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioResponse

router = APIRouter()

@router.get("/perfil/", response_model=UsuarioResponse)
async def obtener_perfil_usuario(
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Obtiene la información completa del perfil del usuario autenticado.
    Incluye datos personales y puntos disponibles.
    """
    Authorize.jwt_required()
    user_dni_str = Authorize.get_jwt_subject()
    
    try:
        user_dni = int(user_dni_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DNI en token JWT inválido."
        )
    
    usuario = db.query(Usuario).filter(Usuario.dni == user_dni).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    return usuario

@router.get("/puntos/", response_model=dict)
async def obtener_puntos_usuario(
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Obtiene únicamente los puntos disponibles del usuario autenticado.
    Endpoint ligero para consultas rápidas de saldo.
    """
    Authorize.jwt_required()
    user_dni_str = Authorize.get_jwt_subject()
    
    try:
        user_dni = int(user_dni_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DNI en token JWT inválido."
        )
    
    usuario = db.query(Usuario).filter(Usuario.dni == user_dni).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    return {
        "dni": usuario.dni,
        "puntos_disponibles": usuario.puntos_disponibles
    }