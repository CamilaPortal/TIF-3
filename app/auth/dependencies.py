from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT

from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.models.usuario import Usuario

def role_required(required_roles: list[str]):
    def dependency(Authorize: AuthJWT = Depends()):
        Authorize.jwt_required()
        claims = Authorize.get_raw_jwt()
        rol = claims.get("rol")

        if rol not in required_roles:
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado: el rol no tiene permisos."
            )
        return claims

    return dependency

def empresa_required():
    """Verifica que el usuario sea de tipo empresa y obtiene su empresa_id"""
    def dependency(
        Authorize: AuthJWT = Depends(),
        db: Session = Depends(get_db)
    ):
        Authorize.jwt_required()
        user_dni_str = Authorize.get_jwt_subject()
        
        try:
            user_dni = int(user_dni_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="DNI en token JWT inválido.")

        usuario = db.query(Usuario).filter(Usuario.dni == user_dni).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
        if usuario.rol != "empresa":
            raise HTTPException(
                status_code=403,
                detail="Acceso denegado: solo usuarios de empresa pueden realizar esta acción."
            )
        
        if not usuario.empresa_id:
            raise HTTPException(
                status_code=400,
                detail="Usuario de empresa sin empresa asignada."
            )

        return {
            "usuario": usuario,
            "empresa_id": usuario.empresa_id
        }

    return dependency
