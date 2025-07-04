from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base


class QRToken(Base):
    __tablename__ = "qr_tokens"

    id = Column(Integer, primary_key=True, index=True)
    id_cesto = Column(String(50), index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True))
    used_at = Column(DateTime(timezone=True), nullable=True) 
    
    peso = Column(Integer, nullable=False) 
    cantidad_botellas = Column(Integer, nullable=False)


    reciclaje_asociado = relationship(
        "Reciclaje", 
        back_populates="qr_token_usado", 
        uselist=False
    )