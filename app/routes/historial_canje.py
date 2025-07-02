import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT

from app.db.connection import get_db
from app.models.usuario import Usuario
from app.models.canje import Canje as CanjeModel
from app.models.empresa import Empresa
from app.models.historialCanje import HistorialCanje as HistorialCanjeModel
from app.schemas.historial_canje import RealizarCanjeRequest, HistorialCanjeResponse, HistorialCanjeDetalladoResponse
from app.services.email_service import EmailService

router = APIRouter()
email_service = EmailService()

def generar_codigo_qr() -> str:
    """Genera código QR único y seguro"""
    timestamp = int(datetime.now().timestamp())
    token_aleatorio = secrets.token_hex(12).upper()
    codigo_qr = f"CANJE-{timestamp}-{token_aleatorio}"
    return codigo_qr

@router.post("/realizar-canje/")
async def realizar_canje(
    canje_id: int,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends()
):
    """
    Permite a un usuario canjear sus puntos por un premio.
    Reduce stock automáticamente y desactiva si llega a 0.
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

    if usuario.rol != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios pueden realizar canjes."
        )

    canje = db.query(CanjeModel).join(Empresa).filter(
        CanjeModel.id == canje_id,
        CanjeModel.is_active == True,
        CanjeModel.stock_actual > 0,
        Empresa.is_active == True
    ).first()
    
    if not canje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canje no encontrado, no disponible o sin stock."
        )

    if usuario.puntos_disponibles < canje.puntos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Puntos insuficientes. Necesitas {canje.puntos} puntos, tienes {usuario.puntos_disponibles}."
        )

    codigo_qr = generar_codigo_qr()
    fecha_vencimiento = datetime.now() + timedelta(days=30)

    nuevo_historial = HistorialCanjeModel(
        puntos_usados=canje.puntos,
        codigo_qr_canje=codigo_qr,
        fecha_canje=datetime.now(),
        fecha_vencimiento=fecha_vencimiento,
        usuario_dni=usuario.dni,
        canje_id=canje.id
    )

    canje.stock_actual -= 1
    if canje.stock_actual <= 0:
        canje.is_active = False

    usuario.puntos_disponibles -= canje.puntos
    db.add(nuevo_historial)
    
    try:
        db.commit()
        db.refresh(nuevo_historial)
        
        email_enviado = email_service.enviar_qr_canje(
            email_destino=usuario.email,
            nombre_usuario=f"{usuario.nombre} {usuario.apellido}",
            premio_nombre=canje.nombre,
            premio_descripcion=canje.descripcion,
            puntos_usados=canje.puntos,
            codigo_qr=codigo_qr,
            empresa_nombre=canje.empresa.nombre,
            empresa_direccion=canje.empresa.direccion,
            fecha_vencimiento=fecha_vencimiento.strftime('%d/%m/%Y')
        )
        
        if not email_enviado:
            print(f"Warning: No se pudo enviar email QR a {usuario.email}")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el canje: {str(e)}"
        )

    mensaje_stock = ""
    if canje.stock_actual <= 0:
        mensaje_stock = f" ¡Felicidades! Obtuviste la última unidad disponible."

    return {
        "message": f"¡Canje realizado exitosamente!{mensaje_stock}",
        "canje_id": nuevo_historial.id,
        "premio": canje.nombre,
        "puntos_usados": canje.puntos,
        "puntos_restantes": usuario.puntos_disponibles,
        "fecha_vencimiento": fecha_vencimiento.strftime('%d/%m/%Y'),
        "stock_info": {
            "stock_restante": canje.stock_actual,
            "agotado": canje.stock_actual <= 0,
            "canje_desactivado": not canje.is_active
        },
        "empresa": {
            "nombre": canje.empresa.nombre,
            "direccion": canje.empresa.direccion
        },
        "email_enviado": email_enviado
    }


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