from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi_jwt_auth import AuthJWT

from app.db.connection import get_db
from app.models.qr_token import QRToken
from app.models.usuario import Usuario
from app.models.reciclaje import Reciclaje
from app.schemas.qr_token import QrTokenGenerate
from app.schemas.reciclaje import ReciclajeConfirmQR, ReciclajeResponse, ReciclajeHistorialResponse

router = APIRouter()

@router.post(
    "/confirmar-escaneo/",
    response_model=ReciclajeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un reciclaje a partir de un QR escaneado y JWT de usuario"
)
async def confirmar_reciclaje_por_qr_app(
    data: ReciclajeConfirmQR,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Confirma y registra un reciclaje.
    Requiere el token del QR escaneado y un JWT válido del usuario.
    """
    Authorize.jwt_required()
    current_user_dni_str = Authorize.get_jwt_subject()
    
    try:
        current_user_dni = int(current_user_dni_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El DNI del usuario en el token JWT no es válido."
        )

    usuario_actual = db.query(Usuario).filter(Usuario.dni == current_user_dni).first()
    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con DNI {current_user_dni} no encontrado."
        )

    qr_token_db = db.query(QRToken).filter(QRToken.token == data.qr_token_value).first()
    if not qr_token_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token QR inválido o no encontrado."
        )
    
    if qr_token_db.is_used:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este token QR ya ha sido utilizado."
        )

    puntos_calculados = (qr_token_db.cantidad_botellas * 1) + int(qr_token_db.peso * 5)

    nuevo_reciclaje = Reciclaje(
        puntos=puntos_calculados,
        usuario_dni=usuario_actual.dni,
        qr_token_id=qr_token_db.id 
    )
    db.add(nuevo_reciclaje)

    qr_token_db.is_used = True
    qr_token_db.used_at = func.now()

    usuario_actual.puntos_disponibles = (usuario_actual.puntos_disponibles or 0) + puntos_calculados

    try:
        db.commit()
        db.refresh(nuevo_reciclaje)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el reciclaje: {str(e)}"
        )

    return nuevo_reciclaje

@router.get("/historial/", response_model=list[ReciclajeHistorialResponse])
async def obtener_historial_reciclajes(
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Obtiene el historial de reciclajes del usuario autenticado.
    Incluye detalles del reciclaje y del QR token usado.
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
    
    # Hacer JOIN para obtener todos los datos necesarios
    reciclajes_query = db.query(
        Reciclaje.id,
        Reciclaje.puntos,
        QRToken.used_at.label('fecha_reciclaje'),  # used_at como fecha_reciclaje
        QRToken.peso,
        QRToken.cantidad_botellas,
        QRToken.id_cesto
    ).join(
        QRToken, Reciclaje.qr_token_id == QRToken.id
    ).filter(
        Reciclaje.usuario_dni == user_dni
    ).order_by(QRToken.used_at.desc())
    
    reciclajes_data = reciclajes_query.all()
    
    # Convertir a diccionarios para que coincidan con el schema
    historial = []
    for r in reciclajes_data:
        historial.append({
            "id": r.id,
            "puntos": r.puntos,
            "fecha_reciclaje": r.fecha_reciclaje,
            "peso": r.peso,
            "cantidad_botellas": r.cantidad_botellas,
            "id_cesto": r.id_cesto
        })
    
    return historial