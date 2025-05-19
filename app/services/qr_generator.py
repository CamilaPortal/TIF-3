import qrcode
from PIL import Image
import os

def guardar_qr_en_archivo(dato: str, ruta_archivo: str):
    contenido = f"Token: {dato}"
    img = qrcode.make(contenido)
    img.save(ruta_archivo, format="PNG")

