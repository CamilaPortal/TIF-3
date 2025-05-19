from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Canje(Base):
    __tablename__ = "canjes"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(255), nullable=False)
    puntos_usados = Column(Integer, nullable=False)
    fecha_canje = Column(DateTime(timezone=True), server_default=func.now())

    usuario_dni = Column(Integer, ForeignKey("usuarios.dni"), nullable=False)

    usuario = relationship("Usuario", back_populates="canjes")