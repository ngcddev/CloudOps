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


settings = Settings()
