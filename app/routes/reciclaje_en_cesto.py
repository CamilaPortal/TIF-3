from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends, status
import uuid
import os
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.models.qr_token import QRToken
from app.schemas.qr_token import QrTokenGenerate
from app.services.qr_generator import guardar_qr_en_archivo

router = APIRouter()


QR_FOLDER = "app/static/qrs"
BASE_URL = "http://192.168.54.142:8001"


@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED, 
    summary="Crea un nuevo token QR con datos iniciales"
)
async def create_qr_token_with_initial_data(
    qr_data: QrTokenGenerate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo registro de QRToken en la base de datos con los datos iniciales
    proporcionados. Genera un token único para este QR.
    Devuelve un mensaje de éxito y el token generado.
    """
    generated_token_value = str(uuid.uuid4())

    new_qr_token_db = QRToken(
        id_cesto=qr_data.cesto_id,
        token=generated_token_value,
        peso=qr_data.peso,
        cantidad_botellas=qr_data.cantidad_botellas,
        is_used=qr_data.is_used
    )

    db.add(new_qr_token_db)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"No se pudo crear el token QR: {str(e)}"
        )

    return {
        "message": "Token QR generado exitosamente",
    }

@router.get(
    "/cesto/{cesto_id}/image", 
    summary="Obtiene la imagen QR del token activo más reciente para un cesto",
)
async def get_qr_image_for_cesto(
    cesto_id: str,
    db: Session = Depends(get_db)
):
    """
    Busca el token QR activo más reciente (no usado y último creado) 
    para el `cesto_id` especificado y devuelve su imagen QR.
    La imagen QR codifica una URL que incluye el token del QR.
    """
    data = db.query(QRToken)\
        .filter(QRToken.id_cesto == cesto_id, QRToken.is_used == False)\
        .order_by(QRToken.created_at.desc())\
        .first()

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un token QR activo para el cesto ID: {cesto_id}"
        )

    qr_filename = f"qr_{data.id_cesto}.png"
    qr_path = os.path.join(QR_FOLDER, qr_filename)
    qr_url = f"{BASE_URL}/static/qrs/{qr_filename}"

    guardar_qr_en_archivo(data.token, qr_path)

    return {
        "cesto_id": data.id_cesto,
        "cantidad_botellas": data.cantidad_botellas,
        "peso": data.peso,
        "qr_url": qr_url
    }