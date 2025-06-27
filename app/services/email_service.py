import os
import qrcode
from io import BytesIO
import base64
from emails import html
from emails.template import JinjaTemplate
from typing import Optional
from app.config.settings import settings

class EmailService:
    def __init__(self):
        # Usar configuración centralizada
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
    
    def generar_qr_canje_attachment(self, codigo_canje: str) -> BytesIO:
        """Genera QR code como BytesIO para attachment"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(codigo_canje)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            print(f"Error generando QR: {str(e)}")
            return None

    def enviar_qr_canje(self, 
                       email_destino: str,
                       nombre_usuario: str,
                       premio_nombre: str,
                       premio_descripcion: str,
                       puntos_usados: int,
                       codigo_qr: str,
                       empresa_nombre: str,
                       empresa_direccion: str,
                       fecha_vencimiento: str) -> bool:
        """Envía código QR de canje al usuario con imagen adjunta"""
        
        print(f"Enviando QR de canje a: {email_destino}")
        
        qr_buffer = self.generar_qr_canje_attachment(codigo_qr)
        
        if not qr_buffer:
            print("Error: No se pudo generar el código QR")
            return False
        
        try:
            template = JinjaTemplate("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>¡Tu Premio Te Está Esperando!</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        max-width: 600px; 
                        margin: 0 auto; 
                        background-color: #f5f5f5;
                    }
                    .email-container {
                        background-color: white;
                        margin: 20px auto;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }
                    .header { 
                        background: linear-gradient(135deg, #4CAF50, #45a049);
                        color: white; 
                        padding: 30px 20px; 
                        text-align: center; 
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 28px;
                    }
                    .content { 
                        padding: 30px 20px; 
                    }
                    .premio-info { 
                        background: #E8F5E8; 
                        padding: 20px; 
                        border-radius: 8px; 
                        margin: 20px 0;
                        border-left: 4px solid #4CAF50;
                    }
                    .qr-section { 
                        background: #f9f9f9; 
                        padding: 30px; 
                        text-align: center; 
                        border-radius: 10px; 
                        margin: 30px 0;
                        border: 2px dashed #4CAF50;
                    }
                    .empresa-info { 
                        background: #E3F2FD; 
                        padding: 20px; 
                        border-radius: 8px; 
                        margin: 20px 0;
                        border-left: 4px solid #2196F3;
                    }
                    .important { 
                        background: #FFF3E0;
                        color: #E65100; 
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                        border-left: 4px solid #FF9800;
                    }
                    .footer { 
                        background: #f0f0f0; 
                        padding: 20px; 
                        text-align: center; 
                        font-size: 14px;
                        color: #666;
                    }
                    .qr-placeholder {
                        background: #f0f0f0;
                        border: 2px dashed #4CAF50;
                        padding: 40px;
                        margin: 20px 0;
                        border-radius: 10px;
                        text-align: center;
                    }
                    .qr-title {
                        font-size: 24px;
                        color: #4CAF50;
                        margin-bottom: 15px;
                        font-weight: bold;
                    }
                    .instrucciones {
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }
                    .instrucciones ol {
                        margin: 0;
                        padding-left: 20px;
                    }
                    .instrucciones li {
                        margin: 8px 0;
                        line-height: 1.5;
                    }
                    .codigo-texto {
                        background: #E8F5E8;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 15px 0;
                        text-align: center;
                    }
                    .codigo-grande {
                        font-size: 18px;
                        font-weight: bold;
                        color: #2E7D32;
                        letter-spacing: 2px;
                        font-family: monospace;
                    }
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🎉 ¡Felicidades {{ nombre_usuario }}!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px;">Tu canje ha sido procesado exitosamente</p>
                    </div>
                    
                    <div class="content">
                        <div class="premio-info">
                            <h3 style="margin-top: 0; color: #2E7D32;">🏆 Tu Premio:</h3>
                            <h4 style="margin: 10px 0; color: #4CAF50;">{{ premio_nombre }}</h4>
                            <p style="margin: 10px 0;">{{ premio_descripcion }}</p>
                            <p style="margin: 10px 0 0 0;"><strong>Puntos utilizados:</strong> <span style="color: #4CAF50; font-weight: bold;">{{ puntos_usados }} pts</span></p>
                        </div>
                        
                        <div class="qr-section">
                            <div class="qr-title">📱 Tu Código QR</div>
                            <div class="qr-placeholder">
                                <h3 style="color: #4CAF50; margin: 0;">📎 Código QR Adjunto</h3>
                                <p style="margin: 10px 0; color: #666;">
                                    Revisa los archivos adjuntos de este email para encontrar tu código QR
                                </p>
                                <p style="margin: 0; font-size: 14px; color: #888;">
                                    Archivo: <strong>qr_canje_{{ codigo_short }}.png</strong>
                                </p>
                            </div>
                            <p style="margin: 20px 0 10px 0; font-size: 18px; font-weight: bold; color: #4CAF50;">
                                Escanea el código QR adjunto en el comercio
                            </p>
                        </div>
                        
                        <div class="codigo-texto">
                            <h3 style="margin-top: 0; color: #2E7D32;">🔢 Código de Referencia:</h3>
                            <div class="codigo-grande">{{ codigo_qr }}</div>
                            <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">
                                Muestra este código si no puedes usar el QR
                            </p>
                        </div>
                        
                        <div class="empresa-info">
                            <h3 style="margin-top: 0; color: #1976D2;">🏪 Dónde Canjear:</h3>
                            <h4 style="margin: 10px 0; color: #2196F3;">{{ empresa_nombre }}</h4>
                            <p style="margin: 5px 0;">📍 {{ empresa_direccion }}</p>
                        </div>
                        
                        <div class="important">
                            <h3 style="margin-top: 0;">⚠️ Información Importante:</h3>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>Vencimiento:</strong> {{ fecha_vencimiento }}</li>
                                <li><strong>Uso único:</strong> Solo se puede usar UNA vez</li>
                                <li><strong>Ubicación:</strong> Solo válido en el comercio indicado</li>
                                <li><strong>Identificación:</strong> Presenta tu DNI para validación</li>
                            </ul>
                        </div>
                        
                        <div class="instrucciones">
                            <h3 style="margin-top: 0; color: #333;">📋 Instrucciones de Canje:</h3>
                            <ol>
                                <li>Descarga la imagen QR adjunta a este email</li>
                                <li>Dirígete al comercio indicado arriba</li>
                                <li>Muestra la imagen QR al personal del establecimiento</li>
                                <li>Alternativamente, dicta el código de referencia</li>
                                <li>Presenta tu DNI para confirmar tu identidad</li>
                                <li>¡Recibe tu premio y disfrútalo! 🎁</li>
                            </ol>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p style="margin: 0 0 10px 0; font-weight: bold;">Sistema de Reciclaje Inteligente</p>
                        <p style="margin: 0;">¡Gracias por reciclar y cuidar el planeta! 🌱♻️</p>
                    </div>
                </div>
            </body>
            </html>
            """)
            
            message = html(
                html=template.render(
                    nombre_usuario=nombre_usuario,
                    premio_nombre=premio_nombre,
                    premio_descripcion=premio_descripcion,
                    puntos_usados=puntos_usados,
                    empresa_nombre=empresa_nombre,
                    empresa_direccion=empresa_direccion,
                    fecha_vencimiento=fecha_vencimiento,
                    codigo_qr=codigo_qr,
                    codigo_short=codigo_qr[-8:]
                ),
                subject=f"🎁 Tu Premio: {premio_nombre} - Código QR de Canje",
                mail_from=self.from_email
            )
            
            message.attach(
                filename=f"qr_canje_{codigo_qr[-8:]}.png",
                content_type="image/png",
                data=qr_buffer.getvalue()
            )
            
            response = message.send(
                to=email_destino,
                smtp={
                    'host': self.smtp_server,
                    'port': self.smtp_port,
                    'user': self.smtp_user,
                    'password': self.smtp_password,
                    'tls': True
                }
            )
            
            return response.status_code == 250
            
        except Exception as e:
            print(f"Error enviando email de QR canje: {str(e)}")
            return False
    
    def enviar_credenciales_empresa(self, 
                                   email_destino: str,
                                   nombre_usuario: str,
                                   email_login: str,
                                   password_temporal: str,
                                   nombre_empresa: str,
                                   direccion_empresa: str) -> bool:
        """Envía credenciales de acceso a usuario empresa"""
        
        try:
            template = JinjaTemplate("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Bienvenido al Sistema de Reciclaje</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                    .header { background: #2E7D32; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .credentials { background: #E8F5E8; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .empresa-info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0; }
                    .footer { background: #f0f0f0; padding: 15px; text-align: center; font-size: 12px; }
                    .important { color: #D32F2F; font-weight: bold; }
                    .credential-item { margin: 8px 0; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🏢 ¡Bienvenido {{ nombre_usuario }}!</h1>
                    <p>Tu cuenta de empresa ha sido creada exitosamente</p>
                </div>
                
                <div class="content">
                    <p>Hola <strong>{{ nombre_usuario }}</strong>,</p>
                    
                    <p>El administrador del sistema ha creado tu cuenta para gestionar los canjes y premios de tu empresa en nuestro Sistema de Reciclaje Inteligente.</p>
                    
                    <div class="empresa-info">
                        <h3>🏢 Información de tu Empresa:</h3>
                        <p><strong>Nombre:</strong> {{ nombre_empresa }}</p>
                        <p><strong>Dirección:</strong> {{ direccion_empresa }}</p>
                    </div>
                    
                    <div class="credentials">
                        <h3>🔑 Tus Credenciales de Acceso:</h3>
                        <div class="credential-item">
                            <strong>Email:</strong> {{ email_login }}
                        </div>
                        <div class="credential-item">
                            <strong>Contraseña temporal:</strong> {{ password_temporal }}
                        </div>
                    </div>
                    
                    <div class="important">
                        <p>⚠️ <strong>IMPORTANTE - Seguridad:</strong></p>
                        <ul>
                            <li>Esta es una contraseña temporal</li>
                            <li>Cambia tu contraseña después del primer login</li>
                            <li>No compartas estas credenciales</li>
                            <li>Mantén tu cuenta segura</li>
                        </ul>
                    </div>
                    
                    <h3>🎯 Como Usuario Empresa puedes:</h3>
                    <ul>
                        <li>✅ Crear y gestionar premios/canjes</li>
                        <li>✅ Actualizar puntos de tus premios</li>
                        <li>✅ Activar/desactivar tus canjes</li>
                        <li>✅ Validar códigos QR de usuarios</li>
                        <li>✅ Ver historial de canjes de tu empresa</li>
                    </ul>
                    
                    <h3>📱 Próximos pasos:</h3>
                    <ol>
                        <li>Ingresa a la aplicación con estas credenciales</li>
                        <li>Cambia tu contraseña temporal</li>
                        <li>Comienza a crear tus primeros premios</li>
                        <li>¡Ayuda a promover el reciclaje! ♻️</li>
                    </ol>
                </div>
                
                <div class="footer">
                    <p>Sistema de Reciclaje Inteligente</p>
                    <p>¡Juntos por un planeta más verde! 🌱</p>
                </div>
            </body>
            </html>
            """)
            
            message = html(
                html=template.render(
                    nombre_usuario=nombre_usuario,
                    email_login=email_login,
                    password_temporal=password_temporal,
                    nombre_empresa=nombre_empresa,
                    direccion_empresa=direccion_empresa
                ),
                subject=f"🏢 Bienvenido al Sistema - Cuenta Empresa {nombre_empresa}",
                mail_from=self.from_email
            )
            
            response = message.send(
                to=email_destino,
                smtp={
                    'host': self.smtp_server,
                    'port': self.smtp_port,
                    'user': self.smtp_user,
                    'password': self.smtp_password,
                    'tls': True
                }
            )
            
            return response.status_code == 250
            
        except Exception as e:
            print(f"Error enviando email de credenciales: {str(e)}")
            return False