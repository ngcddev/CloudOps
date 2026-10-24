# Runner de Gitea Actions para la puerta de seguridad (spec 006, T02).
# Corre los pasos directamente en este contenedor (etiqueta `puerta:host`) y lanza las herramientas
# (Gitleaks, Trivy, Syft, Cosign, Skopeo) como contenedores hermanos con el Docker del equipo, por eso necesita
# el cliente de Docker, git, curl y bash.
FROM gitea/act_runner:0.2.13
RUN apk add --no-cache bash git curl docker-cli jq
