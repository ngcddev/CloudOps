# Configuración de la API: lee las variables de entorno (DATABASE_URL, GITEA_*, ARGOCD_*, GRAFANA_URL…).
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    # Sesiones (spec 007): clave de firma del token; sin ella la API no arranca
    jwt_secret: str
    # Contraseña de desarrollo que el seed aplica a todos los usuarios sembrados (spec 007)
    seed_user_password: str = ""
    # Token con el que el pipeline de seguridad (spec 006) cuenta sus resultados; vacío = no acepta eventos
    pipeline_token: str = ""
    # Costo de bcrypt; las pruebas lo bajan para no tardar
    bcrypt_rounds: int = 12
    # Gitea (spec 005): vacíos = sin conexión; la API arranca y los cambios por GitOps avisan
    gitea_url: str = ""
    gitea_repo: str = "forja-digital/hub-gitops"
    gitea_token: str = ""
    # Argo CD (spec 005): solo lectura del estado de las aplicaciones
    argocd_url: str = ""
    argocd_token: str = ""
    # Minutos que un cambio aprobado puede esperar a quedar publicado y sano antes de pasar a `fallida`
    validation_timeout_minutes: int = 10
    # Direcciones que ve el navegador del técnico (spec 008): enlaces del detalle del incidente a los
    # registros en Grafana y al commit en Gitea. GITEA_PUBLIC_URL no es la GITEA_URL interna del clúster.
    # Vacías = el incidente se muestra sin esos enlaces.
    grafana_url: str = ""
    gitea_public_url: str = ""
    # Webhook de Alertmanager (spec 008): token propio, distinto al de las sesiones y al del pipeline.
    # Vacío = la API arranca pero no acepta avisos.
    alertmanager_token: str = ""
    # Segundos que la regla SitioCaido espera antes de avisar (su `for: 30s` en observability/). El Hub los
    # resta del `startsAt` para que el incidente empiece a la hora real de la caída. Si cambia uno, cambia el otro.
    alert_confirm_seconds: int = 30
    # URL de Prometheus (spec 010): la API consulta el job `sitios` y el de Traefik para los dashboards.
    # Vacío = sin conexión: las tarjetas de disponibilidad responden «sin datos» (CA-8).
    prometheus_url: str = ""


settings = Settings()
