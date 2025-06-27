# Crear archivo app/models/empresa.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.connection import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(500), nullable=True)
    direccion = Column(String(200), nullable=False)
    telefono = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    canjes = relationship("Canje", back_populates="empresa")
    usuarios_empresa = relationship("Usuario", back_populates="empresa")