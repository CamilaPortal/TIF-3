from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.canje import Canje as CanjeModel
from app.models.empresa import Empresa
from app.schemas.canje import (
    CanjeItemResponse, CanjeCreateRequest, CanjeUpdateRequest, 
    CanjeUpdateEstadoRequest, CanjeItemDetalladoResponse
)
from app.auth.dependencies import role_required, empresa_required

router = APIRouter()

@router.get("/disponibles/", 
            response_model=list[CanjeItemDetalladoResponse], 
            summary="Lista todos los premios disponibles para canje con información de empresas")
async def listar_canjes_disponibles(db: Session = Depends(get_db)):
    """Lista todos los canjes activos con información completa de las empresas"""
    canjes_query = db.query(
        CanjeModel.id,
        CanjeModel.nombre,
        CanjeModel.descripcion,
        CanjeModel.puntos,
        CanjeModel.empresa_id,
        Empresa.nombre.label('empresa_nombre'),
        Empresa.direccion.label('empresa_direccion'),
        Empresa.telefono.label('empresa_telefono')
    ).join(
        Empresa, CanjeModel.empresa_id == Empresa.id
    ).filter(
        CanjeModel.is_active == True,
        Empresa.is_active == True
    ).all()
    
    canjes_detallados = []
    for c in canjes_query:
        canjes_detallados.append({
            "id": c.id,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "puntos": c.puntos,
            "empresa_id": c.empresa_id,
            "empresa_nombre": c.empresa_nombre,
            "empresa_direccion": c.empresa_direccion,
            "empresa_telefono": c.empresa_telefono
        })
    
    return canjes_detallados

@router.get("/mi-empresa/", 
            response_model=list[CanjeItemResponse],
            summary="Lista los canjes de mi empresa")
async def listar_mis_canjes(
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """Lista todos los canjes (activos e inactivos) de la empresa del usuario autenticado"""
    canjes_query = db.query(
        CanjeModel.id,
        CanjeModel.nombre,
        CanjeModel.descripcion,
        CanjeModel.puntos,
        CanjeModel.empresa_id,
        Empresa.nombre.label('empresa_nombre')
    ).join(
        Empresa, CanjeModel.empresa_id == Empresa.id
    ).filter(
        CanjeModel.empresa_id == empresa_data["empresa_id"]
    ).all()
    
    mis_canjes = []
    for c in canjes_query:
        mis_canjes.append({
            "id": c.id,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "puntos": c.puntos,
            "empresa_id": c.empresa_id,
            "empresa_nombre": c.empresa_nombre
        })
    
    return mis_canjes

@router.post(
    "/crear/", 
    response_model=CanjeItemResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo ítem de canje (Solo Empresa)"
)
async def crear_nuevo_canje(
    canje_data: CanjeCreateRequest,
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """
    Permite a una empresa crear un nuevo premio disponible para canje.
    El canje se asocia automáticamente a la empresa del usuario autenticado.
    """
    canje_existente = db.query(CanjeModel).filter(
        CanjeModel.nombre == canje_data.nombre,
        CanjeModel.empresa_id == empresa_data["empresa_id"]
    ).first()
    
    if canje_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un canje con el nombre '{canje_data.nombre}' en tu empresa."
        )

    nuevo_canje = CanjeModel(
        nombre=canje_data.nombre,
        descripcion=canje_data.descripcion,
        puntos=canje_data.puntos,
        empresa_id=empresa_data["empresa_id"]
    )
    
    db.add(nuevo_canje)
    try:
        db.commit()
        db.refresh(nuevo_canje)
        
        empresa = db.query(Empresa).filter(Empresa.id == empresa_data["empresa_id"]).first()
        
        return {
            "id": nuevo_canje.id,
            "nombre": nuevo_canje.nombre,
            "descripcion": nuevo_canje.descripcion,
            "puntos": nuevo_canje.puntos,
            "empresa_id": nuevo_canje.empresa_id,
            "empresa_nombre": empresa.nombre
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el ítem de canje: {str(e)}"
        )

@router.put(
    "/{canje_id}/actualizar-puntos/",
    response_model=CanjeItemResponse,
    summary="Actualiza los puntos de un ítem de canje (Solo dueño)"
)
async def actualizar_puntos_canje(
    canje_id: int,
    puntos_data: CanjeUpdateRequest,
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """
    Permite a una empresa actualizar únicamente los puntos de sus propios canjes.
    """
    canje_a_actualizar = db.query(CanjeModel).filter(
        CanjeModel.id == canje_id,
        CanjeModel.empresa_id == empresa_data["empresa_id"]
    ).first()

    if not canje_a_actualizar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canje con ID {canje_id} no encontrado o no pertenece a tu empresa."
        )

    canje_a_actualizar.puntos = puntos_data.puntos
    
    try:
        db.commit()
        db.refresh(canje_a_actualizar)
        
        empresa = db.query(Empresa).filter(Empresa.id == empresa_data["empresa_id"]).first()
        
        return {
            "id": canje_a_actualizar.id,
            "nombre": canje_a_actualizar.nombre,
            "descripcion": canje_a_actualizar.descripcion,
            "puntos": canje_a_actualizar.puntos,
            "empresa_id": canje_a_actualizar.empresa_id,
            "empresa_nombre": empresa.nombre
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar los puntos del ítem de canje: {str(e)}"
        )

@router.put(
    "/{canje_id}/estado/",
    summary="Activa o desactiva un ítem de canje (Solo dueño)"
)
async def gestionar_estado_canje(
    canje_id: int,
    estado_data: CanjeUpdateEstadoRequest,
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """
    Permite a una empresa activar o desactivar sus propios canjes.
    """
    canje_a_gestionar = db.query(CanjeModel).filter(
        CanjeModel.id == canje_id,
        CanjeModel.empresa_id == empresa_data["empresa_id"]
    ).first()

    if not canje_a_gestionar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canje con ID {canje_id} no encontrado o no pertenece a tu empresa."
        )

    if canje_a_gestionar.is_active == estado_data.is_active:
        estado_actual_str = "activo" if canje_a_gestionar.is_active else "inactivo"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El canje ya está {estado_actual_str}."
        )

    canje_a_gestionar.is_active = estado_data.is_active
   
    try:
        db.commit()
        db.refresh(canje_a_gestionar)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado del canje: {str(e)}"
        )
    
    accion_str = "activado" if canje_a_gestionar.is_active else "desactivado"
    return {
        "message": f"Canje '{canje_a_gestionar.nombre}' {accion_str} exitosamente."
    }
