from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Canje(Base):
    __tablename__ = "canje"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500), nullable=False)
    puntos = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    stock_inicial = Column(Integer, nullable=False)
    stock_actual = Column(Integer, nullable=False)
    
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    empresa = relationship("Empresa", back_populates="canjes")