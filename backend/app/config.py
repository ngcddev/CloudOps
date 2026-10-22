# Configuración de la API: lee las variables de entorno (DATABASE_URL, GITEA_*, ARGOCD_*).
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    # Gitea (spec 005): vacíos = sin conexión; la API arranca y los cambios por GitOps avisan
    gitea_url: str = ""
    gitea_repo: str = "forja-digital/hub-gitops"
    gitea_token: str = ""
    # Argo CD (spec 005): solo lectura del estado de las aplicaciones
    argocd_url: str = ""
    argocd_token: str = ""
    # Minutos que un cambio aprobado puede esperar a quedar publicado y sano antes de pasar a `fallida`
    validation_timeout_minutes: int = 10


settings = Settings()
