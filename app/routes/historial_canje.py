from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT

from app.db.connection import get_db
from app.models.usuario import Usuario
from app.models.canje import Canje as CanjeModel
from app.models.historialCanje import HistorialCanje as HistorialCanjeModel
from app.schemas.historial_canje import RealizarCanjeRequest, HistorialCanjeResponse, HistorialCanjeDetalladoResponse

router = APIRouter()

@router.post("/realizar/", response_model=HistorialCanjeResponse, status_code=status.HTTP_201_CREATED)
async def realizar_canje(
    request_data: RealizarCanjeRequest,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    Authorize.jwt_required()
    user_dni_str = Authorize.get_jwt_subject()
    try:
        user_dni = int(user_dni_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DNI en token JWT inválido.")

    usuario = db.query(Usuario).filter(Usuario.dni == user_dni).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    item_a_canjear = db.query(CanjeModel).filter(
        CanjeModel.id == request_data.canje_id,
        CanjeModel.is_active == True
        ).first()
    if not item_a_canjear:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Premio no encontrado.")

    puntos_necesarios = item_a_canjear.puntos

    if usuario.puntos_disponibles < puntos_necesarios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Puntos insuficientes para realizar el canje.")

    usuario.puntos_disponibles -= puntos_necesarios

    nuevo_historial_canje = HistorialCanjeModel(
        usuario_dni=usuario.dni,
        canje_id=item_a_canjear.id,
        puntos_usados=puntos_necesarios,
        # nombre_canje_historial=item_a_canjear.nombre,
        # descripcion_canje_historial=item_a_canjear.descripcion
    )
    db.add(nuevo_historial_canje)

    try:
        db.commit()
        db.refresh(nuevo_historial_canje)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al procesar el canje: {str(e)}")

    return nuevo_historial_canje

@router.get("/", response_model=list[HistorialCanjeDetalladoResponse])
async def obtener_historial_canjes(
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Obtiene el historial completo de canjes del usuario autenticado.
    Incluye detalles del canje realizado y la fecha.
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
    
    # JOIN con la tabla Canje para obtener detalles completos
    historial_query = db.query(
        HistorialCanjeModel.id,
        HistorialCanjeModel.puntos_usados,
        HistorialCanjeModel.fecha_canje,
        HistorialCanjeModel.usuario_dni,
        HistorialCanjeModel.canje_id,
        CanjeModel.nombre.label('canje_nombre'),
        CanjeModel.descripcion.label('canje_descripcion')
    ).join(
        CanjeModel, HistorialCanjeModel.canje_id == CanjeModel.id
    ).filter(
        HistorialCanjeModel.usuario_dni == user_dni
    ).order_by(HistorialCanjeModel.fecha_canje.desc())
    
    historial_data = historial_query.all()
    
    # Convertir a diccionarios para que coincidan con el schema
    historial = []
    for h in historial_data:
        historial.append({
            "id": h.id,
            "puntos_usados": h.puntos_usados,
            "fecha_canje": h.fecha_canje,
            "usuario_dni": h.usuario_dni,
            "canje_id": h.canje_id,
            "canje_nombre": h.canje_nombre,
            "canje_descripcion": h.canje_descripcion
        })
    
    return historial