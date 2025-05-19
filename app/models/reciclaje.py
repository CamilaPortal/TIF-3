from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Reciclaje(Base):
    __tablename__ = "reciclajes"

    id = Column(Integer, primary_key=True, index=True)
    puntos = Column(Integer, nullable=False)


    usuario_dni = Column(Integer, ForeignKey("usuarios.dni"), nullable=False) 
    usuario = relationship("Usuario", back_populates="reciclajes")

    qr_token_id = Column(Integer, ForeignKey("qr_tokens.id"), unique=True, nullable=False)

    qr_token_usado = relationship("QRToken", back_populates="reciclaje_asociado")
