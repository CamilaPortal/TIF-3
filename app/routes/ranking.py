from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi_jwt_auth import AuthJWT

from app.db.connection import get_db
from app.models.usuario import Usuario
from app.models.reciclaje import Reciclaje
from app.models.historialCanje import HistorialCanje
from app.schemas.usuario import UsuarioResponse, UsuarioRankingResponse

router = APIRouter()


@router.get("/puntos-historicos/", response_model=list[UsuarioRankingResponse])
async def obtener_ranking_puntos_historicos(
    limite: int = Query(default=10, ge=1, le=100, description="Número de usuarios a mostrar en el ranking"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el ranking de usuarios ordenados por total de puntos históricos ganados.
    Muestra quiénes han reciclado más a lo largo del tiempo.
    Solo incluye usuarios con rol 'user' que han reciclado al menos una vez.
    """
    
    ranking_query = db.query(
        Usuario.alias,
        Usuario.nombre,
        Usuario.apellido,
        Usuario.puntos_disponibles,
        func.sum(Reciclaje.puntos).label('total_puntos_ganados'),
        func.count(Reciclaje.id).label('total_reciclajes_realizados')
    ).join(
        Reciclaje, Usuario.dni == Reciclaje.usuario_dni
    ).filter(
        Usuario.rol == "user" 
    ).group_by(
        Usuario.dni, Usuario.alias, Usuario.nombre, Usuario.apellido, Usuario.puntos_disponibles
    ).order_by(
        desc(func.sum(Reciclaje.puntos))
    ).limit(limite)
    
    resultados = ranking_query.all()
    
    ranking = []
    for i, usuario in enumerate(resultados, 1):
        ranking.append({
            "posicion": i,
            "alias": usuario.alias,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "puntos_disponibles": usuario.puntos_disponibles,
            "total_puntos_ganados": usuario.total_puntos_ganados,
            "total_reciclajes_realizados": usuario.total_reciclajes_realizados
        })
    
    return ranking


@router.get("/mi-posicion-historica/")
async def obtener_mi_posicion_historica(
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Obtiene la posición del usuario autenticado en el ranking de puntos históricos.
    Solo aplica para usuarios con rol 'user'. Los administradores no participan en rankings.
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
    
    usuario_actual = db.query(Usuario).filter(Usuario.dni == user_dni).first()
    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    if usuario_actual.rol != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los administradores no participan en rankings."
        )
    
    mis_puntos_historicos = db.query(func.coalesce(func.sum(Reciclaje.puntos), 0)).filter(
        Reciclaje.usuario_dni == user_dni
    ).scalar()
    
    total_reciclajes_realizados = db.query(func.count(Reciclaje.id)).filter(
        Reciclaje.usuario_dni == user_dni
    ).scalar()
    
    if mis_puntos_historicos == 0 or total_reciclajes_realizados == 0:
        return {
            "mi_posicion_historica": None,
            "total_usuarios_activos": db.query(
                func.count(func.distinct(Reciclaje.usuario_dni))
            ).join(Usuario, Reciclaje.usuario_dni == Usuario.dni).filter(
                Usuario.rol == "user"
            ).scalar(),
            "mis_puntos_disponibles": usuario_actual.puntos_disponibles,
            "mis_puntos_historicos": 0,
            "mis_reciclajes_realizados": 0,
            "porcentaje_superior": None,
            "mensaje": "Debes reciclar al menos una vez para aparecer en el ranking."
        }
    
    usuarios_con_mas_puntos_historicos = db.query(
        func.count(func.distinct(Reciclaje.usuario_dni))
    ).join(
        Usuario, Reciclaje.usuario_dni == Usuario.dni
    ).filter(
        Usuario.rol == "user"
    ).group_by(
        Reciclaje.usuario_dni
    ).having(
        func.sum(Reciclaje.puntos) > mis_puntos_historicos
    ).count()
    
    mi_posicion_historica = usuarios_con_mas_puntos_historicos + 1
    
    total_usuarios_activos = db.query(
        func.count(func.distinct(Reciclaje.usuario_dni))
    ).join(
        Usuario, Reciclaje.usuario_dni == Usuario.dni
    ).filter(
        Usuario.rol == "user"
    ).scalar()
    
    return {
        "mi_posicion_historica": mi_posicion_historica,
        "total_usuarios_activos": total_usuarios_activos,
        "mis_puntos_disponibles": usuario_actual.puntos_disponibles,
        "mis_puntos_historicos": mis_puntos_historicos,
        "mis_reciclajes_realizados": total_reciclajes_realizados,
        "porcentaje_superior": round((usuarios_con_mas_puntos_historicos / total_usuarios_activos) * 100, 2) if total_usuarios_activos > 0 else 0
    }