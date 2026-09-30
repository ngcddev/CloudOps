# Configuración de la API: lee las variables de entorno (DATABASE_URL, ...).
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str


settings = Settings()
