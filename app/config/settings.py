from pydantic import BaseSettings

class Settings(BaseSettings):
    authjwt_secret_key: str
    authjwt_access_token_expires: int
    
    # Variables de email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    from_email: str

    class Config:
        env_file = ".env"

settings = Settings()