from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT

from app.models import Reciclaje, HistorialCanje, Usuario, QRToken
from app.auth import routes
from app.routes import reciclaje_en_cesto, reciclaje_app, canje, historial_canje, usuario, ranking
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

app.include_router(routes.auth, prefix="/auth", tags=["Auth"])
app.include_router(reciclaje_en_cesto.router, prefix="/reciclaje", tags=["Reciclaje Cesto"])
app.include_router(reciclaje_app.router, prefix="/reciclaje-app", tags=["Reciclaje App"])
app.include_router(canje.router, prefix="/canjes", tags=["Canjes"])
app.include_router(historial_canje.router, prefix="/historial-canje", tags=["Historial Canje"])
app.include_router(usuario.router, prefix="/usuario", tags=["Usuario"])
app.include_router(ranking.router, prefix="/ranking", tags=["Ranking"])



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

