from fastapi import Depends, HTTPException
from fastapi_jwt_auth import AuthJWT

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
