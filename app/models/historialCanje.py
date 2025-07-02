from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class HistorialCanje(Base):
    __tablename__ = "historialCanje"

    id = Column(Integer, primary_key=True, index=True)
    puntos_usados = Column(Integer, nullable=False)
    fecha_canje = Column(DateTime(timezone=True))
    
    codigo_qr_canje = Column(String(100), unique=True, nullable=False)
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    qr_usado = Column(Boolean, default=False, nullable=False)
    fecha_uso = Column(DateTime(timezone=True), nullable=True)

    usuario_dni = Column(Integer, ForeignKey("usuarios.dni"), nullable=False)
    usuario = relationship("Usuario", back_populates="historial_canjes")

    canje_id = Column(Integer, ForeignKey("canje.id"), nullable=False)
    canje = relationship("Canje")

