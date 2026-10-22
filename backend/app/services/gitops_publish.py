# Publicar una versión por GitOps (spec 005, T14): cambia images.newTag del cliente en hub-gitops
# con un único commit. Es lo único que el Hub escribe; Argo CD hace el resto.
import re

from app.integrations.gitea import GiteaClient, version_commit_message
from app.services.kustomization import set_new_tag


class NothingToPublish(Exception):
    """El repositorio ya tiene esa versión: no habría commit que hacer."""


_SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def client_slug(namespace: str) -> str:
    """`cliente-ferreteria` → `ferreteria`: nombre de la carpeta del cliente en hub-gitops.

    Falla (ValueError) si el namespace no es `cliente-<nombre>`: así un dato mal guardado nunca arma una
    ruta fuera de `clients/` ni escribe en un archivo que no es de un cliente.
    """
    slug = namespace.removeprefix("cliente-")
    if slug == namespace or not _SLUG.fullmatch(slug):
        raise ValueError(f"El namespace «{namespace}» no corresponde a un cliente de hub-gitops.")
    return slug


def kustomization_path(namespace: str) -> str:
    return f"clients/{client_slug(namespace)}/kustomization.yaml"


def publish_version(
    gitea: GiteaClient,
    namespace: str,
    tag: str,
    change_id: int,
    author_name: str,
    author_email: str,
) -> str:
    """Escribe `tag` en el kustomization del cliente y devuelve el SHA del commit."""
    path = kustomization_path(namespace)
    current = gitea.get_file(path)
    new_text = set_new_tag(current.text, tag)
    if new_text == current.text:
        raise NothingToPublish(f"{path} ya tiene la versión {tag}.")
    return gitea.update_file(
        path,
        new_text,
        current.sha,
        version_commit_message(client_slug(namespace), tag, change_id),
        author_name,
        author_email,
    )
