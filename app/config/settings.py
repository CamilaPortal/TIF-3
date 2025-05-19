from pydantic import BaseSettings

class Settings(BaseSettings):
    authjwt_secret_key: str
    authjwt_access_token_expires: int

    class Config:
        env_file = ".env"

settings = Settings()
