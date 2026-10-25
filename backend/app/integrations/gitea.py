# Cliente mínimo de la API de Gitea para el repo hub-gitops (spec 005, T11): leer un archivo y
# actualizarlo con un commit. El Hub escribe aquí y en ningún otro lugar (principio 5).
import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from app.config import settings
from app.integrations.http import Transport, urllib_transport


class GiteaError(Exception):
    """Fallo al hablar con Gitea; `status` es el código HTTP o None si no hubo conexión."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class GiteaFile:
    path: str
    text: str
    sha: str  # sha del blob; Gitea lo pide para actualizar y detectar cambios concurrentes


def version_commit_message(client: str, tag: str, change_id: int) -> str:
    """Mensaje del commit de GitOps: `chore(<cliente>): versión <tag> (cambio #<id>)`."""
    return f"chore({client}): versión {tag} (cambio #{change_id})"


def rollback_commit_message(client: str, tag: str, incident_id: int) -> str:
    """Mensaje del commit de rollback: `revert(<cliente>): volver a <tag> (incidente #<id>)` (spec 009)."""
    return f"revert({client}): volver a {tag} (incidente #{incident_id})"


class GiteaClient:
    def __init__(
        self,
        base_url: str,
        repo: str,
        token: str,
        branch: str = "main",
        transport: Transport = urllib_transport,
        timeout: float = 10,
    ):
        if not base_url or not token:
            raise GiteaError("Gitea no está configurado: faltan GITEA_URL o GITEA_TOKEN.")
        self.base_url = base_url.rstrip("/")
        self.repo = repo
        self.token = token
        self.branch = branch
        self.transport = transport
        self.timeout = timeout

    def _call(self, method: str, path: str, body: dict | None = None, query: str = "") -> dict | list:
        """Llama a la API de contenidos de un archivo: /repos/{repo}/contents/{path}."""
        return self._request(method, f"contents/{urllib.parse.quote(path)}{query}", body)

    def _request(self, method: str, resource: str, body: dict | None = None) -> dict | list:
        url = f"{self.base_url}/api/v1/repos/{self.repo}/{resource}"
        path = resource
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"token {self.token}")
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            status, raw = self.transport(request, self.timeout)
        except (urllib.error.URLError, OSError) as error:
            raise GiteaError(f"No hay conexión con Gitea: {error}") from error
        if status >= 400:
            raise GiteaError(f"Gitea respondió {status} en {method} {path}.", status)
        return json.loads(raw or b"{}")

    def head_sha(self) -> str:
        """SHA del último commit de la rama configurada (el que Argo CD toma como revisión)."""
        data = self._request("GET", f"branches/{urllib.parse.quote(self.branch)}")
        return data["commit"]["id"]

    def latest_commit(self, path: str) -> tuple[str, str] | None:
        """(sha, mensaje) del último commit que tocó `path` en la rama, o None si no hay ninguno."""
        query = f"commits?path={urllib.parse.quote(path)}&sha={urllib.parse.quote(self.branch)}&limit=1"
        data = self._request("GET", query)
        if not data:
            return None
        return data[0]["sha"], data[0]["commit"]["message"]

    def get_file(self, path: str) -> GiteaFile:
        """Lee un archivo de la rama configurada."""
        data = self._call("GET", path, query=f"?ref={urllib.parse.quote(self.branch)}")
        return GiteaFile(
            path=path,
            text=base64.b64decode(data["content"]).decode("utf-8"),
            sha=data["sha"],
        )

    def update_file(
        self,
        path: str,
        text: str,
        blob_sha: str,
        message: str,
        author_name: str,
        author_email: str,
    ) -> str:
        """Actualiza un archivo con un único commit y devuelve el SHA del commit."""
        person = {"name": author_name, "email": author_email}
        data = self._call(
            "PUT",
            path,
            {
                "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
                "sha": blob_sha,
                "message": message,
                "branch": self.branch,
                "author": person,
                "committer": person,
            },
        )
        return data["commit"]["sha"]


def gitea_from_settings() -> GiteaClient:
    """Cliente con la configuración del entorno (GITEA_URL, GITEA_REPO, GITEA_TOKEN)."""
    return GiteaClient(settings.gitea_url, settings.gitea_repo, settings.gitea_token)
