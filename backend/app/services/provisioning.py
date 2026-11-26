# Aprovisionamiento de un sitio nuevo por GitOps (spec 016): arma los manifiestos del cliente y los escribe en
# hub-gitops. Es lo único que hace el Hub; el ApplicationSet de Argo CD ve la carpeta nueva y crea el sitio.
from dataclasses import dataclass
from pathlib import Path

from app.integrations.gitea import GiteaClient
from app.models.plan import Plan
from app.models.service import Service
from app.schemas.client import HOST_PATTERN, has_control_chars
from app.services.gitops_publish import client_slug

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "gitops"
REGISTRY_OWNER = "forja-digital"
REGISTRY_IMAGE = "gitea.hub.local/forja-digital"
FIRST_VERSION = "v1"


class AlreadyProvisioned(Exception):
    """La carpeta del cliente ya existe en hub-gitops: no se pisa."""


class InvalidInput(ValueError):
    """La dirección o el nombre del cliente no son seguros para escribirlos en un manifiesto."""


def check_inputs(service: Service) -> None:
    """Defensa en profundidad (auditoría K8-01): aunque el esquema ya valida, un servicio guardado antes de esa regla no debe
    llegar a hub-gitops con un host o un nombre que abra líneas nuevas en el YAML que Argo CD aplica."""
    if not HOST_PATTERN.fullmatch(service.host):
        raise InvalidInput("La dirección (host) del servicio no es un nombre de host válido: corríjala antes de darlo de alta.")
    if has_control_chars(service.project.client.name):
        raise InvalidInput("El nombre del cliente tiene saltos de línea o caracteres de control: corríjalo antes de dar de alta el sitio.")


@dataclass(frozen=True)
class Image:
    base: str   # nombre de la imagen que usa la plantilla (`plantilla`, `plantilla-api`)
    name: str   # imagen real del cliente en el registro


def images_for(service: Service) -> list[Image]:
    """Imágenes que el sitio necesita publicadas: `<cliente>` para landing; `<cliente>-web` y `<cliente>-api` con formulario."""
    slug = client_slug(service.namespace)
    if service.template == "landing_form":
        return [Image("plantilla", f"{slug}-web"), Image("plantilla-api", f"{slug}-api")]
    return [Image("plantilla", slug)]


def render_kustomization(service: Service, plan: Plan) -> str:
    """kustomization.yaml del cliente, con el mismo formato que los de los clientes sembrados."""
    check_inputs(service)
    slug = client_slug(service.namespace)
    form = service.template == "landing_form"
    images = "".join(
        f"  - name: {REGISTRY_IMAGE}/{image.base}\n"
        f"    newName: {REGISTRY_IMAGE}/{image.name}\n"
        f"    newTag: {FIRST_VERSION}\n"
        for image in images_for(service)
    )
    # Con formulario el sitio es un frontend y un backend: el Ingress manda /api al backend
    # y el plan Básico no deja un Pod extra durante la actualización.
    web_strategy = (
        "  - target: { kind: Deployment, name: web }\n"
        "    patch: |-\n"
        "      - op: add\n"
        "        path: /spec/strategy\n"
        "        value:\n"
        "          type: RollingUpdate\n"
        "          rollingUpdate:\n"
        "            maxSurge: 0\n"
        "            maxUnavailable: 1\n"
        if form
        else ""
    )
    api_path = (
        "      - op: add\n"
        "        path: /spec/rules/0/http/paths/-\n"
        "        value:\n"
        "          path: /api\n"
        "          pathType: Prefix\n"
        "          backend:\n"
        "            service:\n"
        "              name: backend\n"
        "              port:\n"
        "                name: http\n"
        if form
        else ""
    )
    return (
        f"# Cliente: {service.project.client.name} · plan {plan.name} ({plan.cpu_quota} / {plan.memory_quota}) · spec 016.\n"
        "# Lo escribió el Hub al dar de alta el sitio; Argo CD lo aplica desde el ApplicationSet `clientes`.\n"
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        f"namespace: {service.namespace}\n"
        "resources:\n"
        "  - ../_base\n"
        + ("  - backend.yaml\n" if form else "")
        + "images:\n"
        + images
        + "patches:\n"
        "  - target: { kind: Namespace }\n"
        "    patch: |-\n"
        "      - op: replace\n"
        "        path: /metadata/name\n"
        f"        value: {service.namespace}\n"
        "      - op: replace\n"
        "        path: /metadata/labels/hub~1client\n"
        f"        value: {slug}\n"
        "      - op: replace\n"
        "        path: /metadata/labels/hub~1plan\n"
        f"        value: {plan.code}\n"
        "  - target: { kind: ResourceQuota }\n"
        "    patch: |-\n"
        "      - op: replace\n"
        "        path: /spec/hard/limits.cpu\n"
        f"        value: {plan.cpu_quota}\n"
        "      - op: replace\n"
        "        path: /spec/hard/limits.memory\n"
        f"        value: {plan.memory_quota}\n"
        + web_strategy
        + "  - target: { kind: Ingress }\n"
        "    patch: |-\n"
        "      - op: replace\n"
        "        path: /spec/rules/0/host\n"
        f"        value: {service.host}\n"
        + api_path
    )


def render_catalog_info(service: Service, plan: Plan) -> str:
    """Entrada de Backstage del sitio (RF-22), con el mismo formato que la de los clientes sembrados. Argo CD la ignora."""
    check_inputs(service)
    slug = client_slug(service.namespace)
    cliente = service.project.client.name
    lineas = [
        f"# Entrada de Backstage de {cliente} (spec 016, RF-22). La escribió el Hub al dar de alta el sitio; Argo CD la ignora",
        "# porque kustomization.yaml no la incluye.",
        "apiVersion: backstage.io/v1alpha1",
        "kind: Component",
        "metadata:",
        f"  name: {slug}",
        f"  title: {cliente} · sitio web",
        f"  description: Sitio web de {cliente}, operado por Forja Digital (plan {plan.name}).",
        "  annotations:",
        "    hub.local/console-url: http://hub.local/agencia/servicios",
        f"    backstage.io/source-location: url:http://gitea.hub.local/forja-digital/hub-gitops/src/branch/main/clients/{slug}/",
        "  links:",
        "    - url: http://hub.local/agencia/servicios",
        "      title: Hub · estado del servicio",
        f"    - url: http://{service.host}",
        "      title: Sitio del cliente",
        "  tags:",
        "    - sitio-web",
        f"    - {plan.code}",
        "spec:",
        "  type: website",
        "  lifecycle: production",
        "  owner: forja-digital",
    ]
    salto = chr(10)
    return salto.join(lineas) + salto


def render_files(service: Service, plan: Plan) -> dict[str, str]:
    """Ruta en hub-gitops → contenido, de todo lo que el sitio necesita."""
    slug = client_slug(service.namespace)
    files = {
        f"clients/{slug}/catalog-info.yaml": render_catalog_info(service, plan),
        f"clients/{slug}/kustomization.yaml": render_kustomization(service, plan),
    }
    if service.template == "landing_form":
        files[f"clients/{slug}/backend.yaml"] = (ASSETS / "landing_form_backend.yaml").read_text(encoding="utf-8")
    return files


def missing_images(gitea: GiteaClient, service: Service) -> list[str]:
    """Imágenes `<nombre>:v1` que el registro dice que no existen (si no se puede saber, no se bloquea)."""
    return [
        f"{image.name}:{FIRST_VERSION}"
        for image in images_for(service)
        if gitea.image_exists(REGISTRY_OWNER, image.name, FIRST_VERSION) is False
    ]


def provision_message(slug: str, client_name: str) -> str:
    return f"feat({slug}): alta del sitio de {client_name}"


def provision(gitea: GiteaClient, service: Service, plan: Plan, author_name: str, author_email: str) -> list[str]:
    """Escribe los archivos del sitio en hub-gitops y devuelve los SHA de los commits, en orden.

    El kustomization va al final: es el que hace que el ApplicationSet vea la carpeta, y para entonces el
    resto ya está. Si la carpeta ya tiene su kustomization no se escribe nada (AlreadyProvisioned).
    """
    files = render_files(service, plan)
    kustomization = next(path for path in files if path.endswith("kustomization.yaml"))
    if gitea.file_exists(kustomization):
        raise AlreadyProvisioned(f"{kustomization} ya existe en hub-gitops.")
    message = provision_message(client_slug(service.namespace), service.project.client.name)
    ordered = [path for path in files if path != kustomization] + [kustomization]
    return [gitea.create_file(path, files[path], message, author_name, author_email) for path in ordered]
