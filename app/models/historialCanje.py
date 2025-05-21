from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class HistorialCanje(Base):
    __tablename__ = "historialCanje"

    id = Column(Integer, primary_key=True, index=True)
    puntos_usados = Column(Integer, nullable=False)
    fecha_canje = Column(DateTime(timezone=True), server_default=func.now())

    # nombre_canje_historial = Column(String(500), nullable=False) 
    # descripcion_canje_historial = Column(String(255), nullable=True)

    usuario_dni = Column(Integer, ForeignKey("usuarios.dni"), nullable=False)
    usuario = relationship("Usuario", back_populates="historial_canjes")

    canje_id = Column(Integer, ForeignKey("canje.id"), nullable=False)

