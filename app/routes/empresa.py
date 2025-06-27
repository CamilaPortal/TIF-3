# En app/routes/empresa.py - corregir el endpoint
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
import secrets
import string
from datetime import datetime

from app.db.connection import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.canje import Canje as CanjeModel
from app.models.historialCanje import HistorialCanje as HistorialCanjeModel
from app.schemas.empresa import EmpresaCreateRequest, EmpresaResponse, EmpresaUsuarioCreateRequest
from app.schemas.validacion_qr_empresa import ValidarQRRequest, ConfirmarEntregaRequest
from app.auth.dependencies import role_required, empresa_required
from app.services.email_service import EmailService

router = APIRouter()
email_service = EmailService()

def generar_password_temporal() -> str:
    """Genera una contraseña temporal segura"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))

@router.post("/crear/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def crear_empresa(
    empresa_data: EmpresaCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin"]))
):
    """
    Crea una nueva empresa en el sistema.
    Solo administradores del sistema pueden crear empresas.
    """
    empresa_existente = db.query(Empresa).filter(Empresa.nombre == empresa_data.nombre).first()
    if empresa_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una empresa con el nombre '{empresa_data.nombre}'."
        )

    empresa_email_existente = db.query(Empresa).filter(Empresa.email == empresa_data.email).first()
    if empresa_email_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una empresa con el email '{empresa_data.email}'."
        )

    nueva_empresa = Empresa(
        nombre=empresa_data.nombre,
        descripcion=empresa_data.descripcion,
        direccion=empresa_data.direccion,
        telefono=empresa_data.telefono,
        email=empresa_data.email
    )
    
    db.add(nueva_empresa)
    try:
        db.commit()
        db.refresh(nueva_empresa)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la empresa: {str(e)}"
        )
    
    return nueva_empresa

@router.post("/usuario/", status_code=status.HTTP_201_CREATED)
async def crear_usuario_empresa(
    usuario_data: EmpresaUsuarioCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(role_required(["admin"]))
):
    """
    Crea un usuario asociado a una empresa y envía credenciales por email.
    Este usuario podrá gestionar los canjes de su empresa.
    """
    empresa = db.query(Empresa).filter(Empresa.id == usuario_data.empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada."
        )

    usuario_por_dni = db.query(Usuario).filter(Usuario.dni == usuario_data.dni).first()
    if usuario_por_dni:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="DNI ya registrado."
        )
    
    usuario_por_email = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if usuario_por_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Correo electrónico ya registrado."
        )

    usuario_por_alias = db.query(Usuario).filter(Usuario.alias == usuario_data.alias).first()
    if usuario_por_alias:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Alias ya registrado."
        )

    password_temporal = usuario_data.password if usuario_data.password else generar_password_temporal()

    nuevo_usuario = Usuario(
        dni=usuario_data.dni,
        alias=usuario_data.alias,
        nombre=usuario_data.nombre,
        apellido=usuario_data.apellido,
        telefono=usuario_data.telefono,
        email=usuario_data.email,
        rol="empresa",
        empresa_id=usuario_data.empresa_id
    )
    nuevo_usuario.set_password(password_temporal)

    db.add(nuevo_usuario)
    try:
        db.commit()
        db.refresh(nuevo_usuario)
        
        email_enviado = email_service.enviar_credenciales_empresa(
            email_destino=nuevo_usuario.email,
            nombre_usuario=f"{nuevo_usuario.nombre} {nuevo_usuario.apellido}",
            email_login=nuevo_usuario.email,
            password_temporal=password_temporal,
            nombre_empresa=empresa.nombre,
            direccion_empresa=empresa.direccion
        )
        
        if not email_enviado:
            print(f"Warning: No se pudo enviar email a {nuevo_usuario.email}")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el usuario de empresa: {str(e)}"
        )

    return {
        "message": f"Usuario de empresa creado exitosamente para {empresa.nombre}",
        "usuario_dni": nuevo_usuario.dni,
        "empresa": empresa.nombre,
        "email_enviado": email_enviado,
        "nota": "Las credenciales han sido enviadas al email del usuario" if email_enviado else "Usuario creado pero no se pudo enviar email"
    }

@router.get("/", response_model=list[EmpresaResponse])
async def listar_empresas(
    db: Session = Depends(get_db)
):
    """Lista todas las empresas activas del sistema"""
    empresas = db.query(Empresa).filter(Empresa.is_active == True).all()
    return empresas

@router.post("/validar-qr/")
async def validar_qr_canje(
    request_data: ValidarQRRequest,
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """
    Permite a una empresa validar un código QR de canje.
    Verifica que el QR sea válido, no haya sido usado y corresponda a un canje de su empresa.
    """
    
    codigo_qr = request_data.codigo_qr
    print(f"Validando QR: {codigo_qr} para empresa ID: {empresa_data['empresa_id']}")
    
    historial_canje = db.query(HistorialCanjeModel).join(
        CanjeModel, HistorialCanjeModel.canje_id == CanjeModel.id
    ).join(
        Usuario, HistorialCanjeModel.usuario_dni == Usuario.dni
    ).filter(
        HistorialCanjeModel.codigo_qr_canje == codigo_qr
    ).first()
    
    if not historial_canje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código QR no encontrado o inválido."
        )
    
    if historial_canje.qr_usado:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Este código QR ya fue utilizado el {historial_canje.fecha_uso.strftime('%d/%m/%Y %H:%M')}."
        )
    
    if historial_canje.fecha_vencimiento < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Este código QR venció el {historial_canje.fecha_vencimiento.strftime('%d/%m/%Y')}."
        )
    
    if historial_canje.canje.empresa_id != empresa_data["empresa_id"]:
        empresa_correcta = historial_canje.canje.empresa.nombre
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Este premio pertenece a '{empresa_correcta}', no a tu empresa."
        )
    
    usuario = historial_canje.usuario
    canje = historial_canje.canje
    
    return {
        "valid": True,
        "message": "Código QR válido y listo para canjear",
        "canje_info": {
            "id": historial_canje.id,
            "premio": canje.nombre,
            "descripcion": canje.descripcion,
            "puntos_usados": historial_canje.puntos_usados,
            "fecha_canje": historial_canje.fecha_canje.strftime('%d/%m/%Y %H:%M'),
            "fecha_vencimiento": historial_canje.fecha_vencimiento.strftime('%d/%m/%Y')
        },
        "usuario_info": {
            "dni": usuario.dni,
            "nombre": f"{usuario.nombre} {usuario.apellido}",
            "email": usuario.email
        },
        "empresa_info": {
            "nombre": canje.empresa.nombre,
            "direccion": canje.empresa.direccion
        },
        "instrucciones": [
            f"Verificar DNI del usuario: {usuario.dni}",
            f"Entregar: {canje.nombre}",
            "Confirmar la entrega usando el endpoint /confirmar-entrega/"
        ]
    }

@router.post("/confirmar-entrega/")
async def confirmar_entrega_premio(
    request_data: ConfirmarEntregaRequest,
    empresa_data: dict = Depends(empresa_required()),
    db: Session = Depends(get_db)
):
    """
    Confirma la entrega del premio después de validar el QR.
    Marca el QR como usado y registra la fecha de uso.
    """
    
    codigo_qr = request_data.codigo_qr 
    
    historial_canje = db.query(HistorialCanjeModel).join(
        CanjeModel, HistorialCanjeModel.canje_id == CanjeModel.id
    ).filter(
        HistorialCanjeModel.codigo_qr_canje == codigo_qr,
        CanjeModel.empresa_id == empresa_data["empresa_id"]
    ).first()
    
    if not historial_canje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código QR no encontrado o no pertenece a tu empresa."
        )
    
    if historial_canje.qr_usado:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este código QR ya fue utilizado anteriormente."
        )
    
    if historial_canje.fecha_vencimiento < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este código QR ha vencido y no se puede usar."
        )
    
    historial_canje.qr_usado = True
    historial_canje.fecha_uso = datetime.now()
    historial_canje.empresa_validadora_id = empresa_data["empresa_id"]
    
    try:
        db.commit()
        db.refresh(historial_canje)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al confirmar la entrega: {str(e)}"
        )
    
    usuario = historial_canje.usuario
    canje = historial_canje.canje
    
    return {
        "success": True,
        "message": "¡Premio entregado exitosamente!",
        "entrega_confirmada": {
            "premio": canje.nombre,
            "usuario": f"{usuario.nombre} {usuario.apellido}",
            "dni_usuario": usuario.dni,
            "fecha_entrega": historial_canje.fecha_uso.strftime('%d/%m/%Y %H:%M'),
            "puntos_canjeados": historial_canje.puntos_usados
        },
        "qr_status": "USADO - No se puede volver a utilizar"
    }