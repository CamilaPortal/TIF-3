from passlib.hash import bcrypt
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.connection import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    dni = Column(Integer, primary_key=True)
    alias = Column(String(25), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    puntos_disponibles = Column(Integer, default=0, nullable=False)
    email = Column(String(250), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False) 
    telefono = Column(Integer, nullable=False)
    rol = Column(String(10), nullable=True)

    historial_canjes = relationship("HistorialCanje", back_populates="usuario")
    reciclajes = relationship("Reciclaje", back_populates="usuario")

    def set_password(self, raw_password):
        self.password = bcrypt.hash(raw_password)

    def check_password(self, raw_password):
        return bcrypt.verify(raw_password, self.password)