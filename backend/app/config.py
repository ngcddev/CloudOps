# Configuración de la API: lee las variables de entorno (DATABASE_URL, GITEA_*, ARGOCD_*).
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    # Gitea (spec 005): vacíos = sin conexión; la API arranca y los cambios por GitOps avisan
    gitea_url: str = ""
    gitea_repo: str = "forja-digital/hub-gitops"
    gitea_token: str = ""


settings = Settings()
