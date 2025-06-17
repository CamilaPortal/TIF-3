from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.canje import Canje as CanjeModel
from app.schemas.canje import CanjeItemResponse, CanjeCreateRequest, CanjeUpdateRequest, CanjeUpdateEstadoRequest
from app.auth.dependencies import role_required

router = APIRouter()

@router.get("/disponibles/", 
            response_model=list[CanjeItemResponse], 
            summary="Lista todos los premios disponibles para canje")
async def listar_canjes_disponibles(db: Session = Depends(get_db)):
    canjes = db.query(CanjeModel).filter(CanjeModel.is_active == True).all()
    return canjes

@router.post(
    "/crear/", 
    response_model=CanjeItemResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo ítem de canje (Solo Admin)",
    dependencies=[Depends(role_required(["admin"]))]
)
async def crear_nuevo_canje(
    canje_data: CanjeCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Permite a un administrador crear un nuevo premio disponible para canje.
    Requiere rol 'admin'.
    """

    canje_existente = db.query(CanjeModel).filter(CanjeModel.nombre == canje_data.nombre).first()
    if canje_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un ítem de canje con el nombre '{canje_data.nombre}'."
        )

    nuevo_canje = CanjeModel(
        nombre=canje_data.nombre,
        descripcion=canje_data.descripcion,
        puntos=canje_data.puntos
    )
    db.add(nuevo_canje)
    try:
        db.commit()
        db.refresh(nuevo_canje)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el ítem de canje: {str(e)}"
        )
    return nuevo_canje

@router.put(
    "/{canje_id}/actualizar-puntos/",
    response_model=CanjeItemResponse,
    summary="Actualiza los puntos de un ítem de canje (Solo Admin)",
    dependencies=[Depends(role_required(["admin"]))]
)
async def actualizar_puntos_canje(
    canje_id: int,
    puntos_data: CanjeUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Permite a un administrador actualizar únicamente los puntos de un ítem de canje.
    Requiere rol 'admin'.
    """
    canje_a_actualizar = db.query(CanjeModel).filter(CanjeModel.id == canje_id).first()

    if not canje_a_actualizar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ítem de canje con ID {canje_id} no encontrado."
        )

    canje_a_actualizar.puntos = puntos_data.puntos
    
    try:
        db.commit()
        db.refresh(canje_a_actualizar)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar los puntos del ítem de canje: {str(e)}"
        )
    return canje_a_actualizar

@router.put(
    "/{canje_id}/estado/",
    summary="Activa o desactiva un ítem de canje (Solo Admin)",
    dependencies=[Depends(role_required(["admin"]))]
)
async def gestionar_estado_canje(
    canje_id: int,
    estado_data: CanjeUpdateEstadoRequest,
    db: Session = Depends(get_db)
):
    """
    Permite a un administrador activar o desactivar un ítem de canje.
    - Para activar: Enviar {"is_active": true}
    - Para desactivar: Enviar {"is_active": false}
    Requiere rol 'admin'.
    """
    canje_a_gestionar = db.query(CanjeModel).filter(CanjeModel.id == canje_id).first()

    if not canje_a_gestionar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ítem de canje con ID {canje_id} no encontrado."
        )

    if canje_a_gestionar.is_active == estado_data.is_active:
        estado_actual_str = "activo" if canje_a_gestionar.is_active else "inactivo"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ítem de canje con ID {canje_id} ya está {estado_actual_str}."
        )

    canje_a_gestionar.is_active = estado_data.is_active
   
    try:
        db.commit()
        db.refresh(canje_a_gestionar)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado del ítem de canje: {str(e)}"
        )
    
    accion_str = "activado" if canje_a_gestionar.is_active else "desactivado"
    return canje_a_gestionar