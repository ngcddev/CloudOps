# Cliente de solo lectura de la API de Argo CD (spec 005, T12): sincronización, salud y revisión
# de una aplicación. El Hub nunca habla con Kubernetes: el estado se lee de aquí, no se infiere.
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from app.config import settings
from app.integrations.http import Transport, urllib_transport


class ArgoCDError(Exception):
    """Fallo al hablar con Argo CD; `status` es el código HTTP o None si no hubo conexión."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class AppStatus:
    sync: str  # Synced | OutOfSync | Unknown
    health: str  # Healthy | Progressing | Degraded | Missing | Suspended | Unknown
    revision: str | None  # SHA del commit de hub-gitops que Argo CD aplicó


class ArgoCDClient:
    def __init__(self, base_url: str, token: str, transport: Transport = urllib_transport, timeout: float = 10):
        if not base_url or not token:
            raise ArgoCDError("Argo CD no está configurado: faltan ARGOCD_URL o ARGOCD_TOKEN.")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.transport = transport
        self.timeout = timeout

    def get_application(self, name: str) -> AppStatus:
        """Lee el estado de la aplicación `name` (por convención, el namespace del cliente)."""
        url = f"{self.base_url}/api/v1/applications/{urllib.parse.quote(name)}"
        request = urllib.request.Request(url, method="GET")
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("Accept", "application/json")
        try:
            status, raw = self.transport(request, self.timeout)
        except (urllib.error.URLError, OSError) as error:
            raise ArgoCDError(f"No hay conexión con Argo CD: {error}") from error
        if status == 404:
            raise ArgoCDError(f"Argo CD no tiene la aplicación «{name}».", status)
        if status >= 400:
            raise ArgoCDError(f"Argo CD respondió {status} al consultar «{name}».", status)
        state = json.loads(raw or b"{}").get("status", {})
        sync = state.get("sync", {})
        return AppStatus(
            sync=sync.get("status", "Unknown"),
            health=state.get("health", {}).get("status", "Unknown"),
            revision=sync.get("revision"),
        )


def argocd_from_settings() -> ArgoCDClient:
    """Cliente con la configuración del entorno (ARGOCD_URL, ARGOCD_TOKEN)."""
    return ArgoCDClient(settings.argocd_url, settings.argocd_token)
