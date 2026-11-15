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
    # Segregación de funciones (spec 018): quien pide un cambio de versión no puede aprobarlo; lo aprueba otra persona de la agencia.
    # Activa por defecto; solo se apaga (SEGREGACION_FUNCIONES=false) en un laboratorio con una sola cuenta de agencia.
    segregacion_funciones: bool = True
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
    # URL de Loki (spec 019): el diagnóstico con IA lee las últimas líneas de registro del cliente. Vacío = sin registros como evidencia.
    loki_url: str = ""
    # Servicio de voz (spec 021): voz a texto y texto a voz en CPU. Vacío = el asistente solo funciona por texto. El token, si se define, lo exige el servicio.
    voz_url: str = ""
    voz_token: str = ""
    # Trazas (OpenTelemetry): URL base del receptor OTLP/HTTP de Tempo, por ejemplo http://tempo.monitoring.svc:4318. Vacío = sin trazas.
    otel_exporter_otlp_endpoint: str = ""
    # Asistente local (spec 012): Ollama en el PC B. Vacío = el asistente responde que la IA no está disponible.
    ollama_url: str = ""
    ollama_model: str = "qwen2.5:7b-instruct"
    # Cuánto tiempo deja Ollama el modelo en VRAM tras responder (el PC B comparte GPU con ComfyUI)
    ollama_keep_alive: str = "2m"
    assistant_timeout_seconds: int = 60
    # P(fuera de tema) mínima para saltarse el LLM; 0 = usar el umbral con que se entrenó el modelo
    # Endpoint de `mlflow models serve` con la compuerta (spec 016); vacío = se usa el JSON local de backend/app/assets
    gate_model_url: str = ""
    assistant_gate_threshold: float = 0
    # Contexto del LLM: "completo" le pasa toda la ayuda (lo más fiable mientras quepa en el modelo),
    # "recuperacion" solo las secciones más parecidas por palabras (léxico, sin Ollama) y "rag" las más parecidas por
    # significado (embeddings de Ollama + índice guardado en la base). Si el RAG no puede (Ollama apagado o sin
    # índice), cae a "recuperacion" y lo deja anotado en ai_queries.context_mode.
    assistant_context_mode: str = "completo"
    # RAG (spec 012): modelo de embeddings servido por el mismo Ollama, cuántos trozos se recuperan y la similitud
    # coseno mínima del mejor trozo; por debajo no se llama al LLM («sin información»). Calibrado con el barrido de
    # ai/eval/run_eval.py: hasta 0,66 no se pierde ninguna recuperación; se usa 0,60 de margen. El umbral solo descarta
    # lo claramente ajeno; lo cercano pero no cubierto lo resuelve el prompt estricto del LLM («No tengo esa información»).
    ollama_embed_model: str = "nomic-embed-text"
    rag_top_k: int = 4
    rag_min_score: float = 0.60
    # Pool de conexiones a PostgreSQL (auditoría BE-02): con el pool por defecto (5 + 10) unas 15 peticiones lentas a la vez dejaban a las demás
    # esperando 30 s y fallando. Esperar una conexión más de DB_POOL_TIMEOUT segundos falla rápido, y la base corta lo que se queda colgado.
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: int = 10
    # Milisegundos que puede tardar una sola sentencia, y que puede quedar una transacción abierta sin hacer nada (una conexión «idle in transaction»).
    # Lo segundo es una red de seguridad por si algo olvida cerrar: debe superar con holgura lo que tarda una llamada lenta que sí la sostiene
    # (diagnóstico con Prometheus, Loki y Ollama; altas con Gitea), por eso son 5 minutos.
    db_statement_timeout_ms: int = 15000
    db_idle_in_transaction_timeout_ms: int = 300000
    # Tope del cuerpo de una petición (auditoría BE-05), con el Ingress directo al Pod de 256 Mi: lo general, el informe del pipeline (Trivy y SBOM
    # miden unos 600 KB) y el audio de voz (2 MB más lo que añade el formato).
    body_limit_bytes: int = 1_048_576
    pipeline_body_limit_bytes: int = 8_388_608
    voice_body_limit_bytes: int = 2_100_000


JWT_SECRET_MIN_LENGTH = 32
# Prefijo del valor de .env.example: está publicado en el repositorio, así que no sirve para firmar sesiones (auditoría CT-01)
JWT_SECRET_EJEMPLO = "clave-de-desarrollo-cambiala"


def validar_jwt_secret(valor: str) -> None:
    """Rechaza una clave de firma corta o la del ejemplo. La API la llama al arrancar; los scripts de `ai/` solo importan `settings`."""
    como_generar = 'Genera una con: python -c "import secrets; print(secrets.token_urlsafe(48))" y ponla en JWT_SECRET de tu .env.'
    if valor.startswith(JWT_SECRET_EJEMPLO):
        raise RuntimeError(f"JWT_SECRET es el valor de ejemplo de .env.example, que está publicado en el repositorio. {como_generar}")
    if len(valor) < JWT_SECRET_MIN_LENGTH:
        raise RuntimeError(f"JWT_SECRET tiene {len(valor)} caracteres y debe tener al menos {JWT_SECRET_MIN_LENGTH}. {como_generar}")


settings = Settings()
