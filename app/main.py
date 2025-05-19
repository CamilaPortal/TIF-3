from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT

from app.models import Reciclaje, Canje, Usuario, QRToken
from app.auth import routes
from app.routes import reciclaje
from app.config.settings import settings
from app.db.connection import Base, engine

app = FastAPI(
    title="API Reciclaje Inteligente",
    description="API para registrar eventos de reciclaje desde Arduino y generar QR para validar puntos.",
    version="1.0.0"
)

@AuthJWT.load_config
def get_config():
    return settings

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(reciclaje.router, prefix="/reciclaje", tags=["Reciclaje"])
app.include_router(routes.auth, prefix="/auth", tags=["Auth"])
#app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

