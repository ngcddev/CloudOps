# Pruebas del alta de un sitio por GitOps (spec 016): los manifiestos que escribe el Hub son los mismos que
# los de los clientes sembrados, se escriben una sola vez y nunca sin la imagen publicada.
from pathlib import Path

import pytest
from sqlalchemy import select

from app.integrations.gitea import GiteaClient
from app.models.service import Service
from app.routers.change_requests import get_gitea
from app.services import provisioning
from tests.fake_gitea import FakeGitea

CLIENTES = Path(__file__).resolve().parents[2] / "gitops" / "clients"


@pytest.fixture
def client(as_agency):
    return as_agency


@pytest.fixture
def gitea():
    with FakeGitea({}) as fake:
        from app.main import app

        app.dependency_overrides[get_gitea] = lambda: GiteaClient(fake.url, fake.repo, fake.token)
        yield fake
        app.dependency_overrides.pop(get_gitea, None)


def _sin_comentarios(texto: str) -> str:
    """Sin las líneas de comentario del encabezado: lo demás debe ser idéntico."""
    return "".join(linea for linea in texto.splitlines(keepends=True) if not linea.lstrip().startswith("#"))


@pytest.mark.parametrize("namespace, carpeta", [
    ("cliente-restaurante", "restaurante"),   # landing, plan Premium
    ("cliente-ferreteria", "ferreteria"),     # landing, plan Estándar
    ("cliente-consultorio", "consultorio"),   # landing con formulario, plan Básico
])
def test_el_kustomization_generado_es_el_de_los_clientes_sembrados(seeded, namespace, carpeta):
    service = seeded.scalar(select(Service).where(Service.namespace == namespace))
    real = (CLIENTES / carpeta / "kustomization.yaml").read_text(encoding="utf-8")
    generado = provisioning.render_kustomization(service, service.plan)
    assert _sin_comentarios(generado) == _sin_comentarios(real)


def test_con_formulario_se_escribe_tambien_el_backend(seeded):
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-consultorio"))
    archivos = provisioning.render_files(service, service.plan)
    assert set(archivos) == {"clients/consultorio/kustomization.yaml", "clients/consultorio/backend.yaml", "clients/consultorio/catalog-info.yaml"}
    assert archivos["clients/consultorio/backend.yaml"] == (CLIENTES / "consultorio" / "backend.yaml").read_text(encoding="utf-8")


@pytest.mark.parametrize("namespace, carpeta", [
    ("cliente-restaurante", "restaurante"),
    ("cliente-ferreteria", "ferreteria"),
    ("cliente-consultorio", "consultorio"),
])
def test_la_entrada_de_backstage_es_la_de_los_clientes_sembrados(seeded, namespace, carpeta):
    service = seeded.scalar(select(Service).where(Service.namespace == namespace))
    real = (CLIENTES / carpeta / "catalog-info.yaml").read_text(encoding="utf-8")
    generado = provisioning.render_catalog_info(service, service.plan)
    # `metadata.name` de los sembrados lleva el nombre largo del cliente; el generado usa el nombre de la carpeta
    assert _sin_comentarios(yaml_sin_nombre(generado)) == _sin_comentarios(yaml_sin_nombre(real))


def yaml_sin_nombre(texto: str) -> str:
    return "".join(linea for linea in texto.splitlines(keepends=True) if not linea.startswith("  name:"))


def _crear_sitio(client, plantilla: str = "landing_form") -> dict:
    cliente = client.post("/api/clients", json={"name": "Colegio San Marcos", "email": "rectoria@sanmarcos.test"}).json()
    proyecto = client.post(f"/api/clients/{cliente['id']}/projects", json={"name": "Sitio del colegio"}).json()
    plan = next(p for p in client.get("/api/plans").json() if p["code"] == "basico")
    respuesta = client.post(
        f"/api/projects/{proyecto['id']}/services",
        json={"name": "Landing con inscripciones", "host": "colegio.hub.local", "template": plantilla,
              "namespace": "cliente-colegio", "plan_id": plan["id"]},
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def test_dar_de_alta_escribe_los_archivos_con_el_backend_primero(client, seeded, gitea):
    servicio = _crear_sitio(client)
    respuesta = client.post(f"/api/services/{servicio['id']}/provision")
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["namespace"] == "cliente-colegio" and len(cuerpo["commits"]) == 3
    assert set(gitea.files) == {"clients/colegio/kustomization.yaml", "clients/colegio/backend.yaml", "clients/colegio/catalog-info.yaml"}
    # El kustomization es lo último: el ApplicationSet no ve la carpeta hasta que todo está
    assert [c["path"] for c in gitea.commits][-1] == "clients/colegio/kustomization.yaml"
    assert "colegio-web" in gitea.files["clients/colegio/kustomization.yaml"]
    assert "colegio-api" in gitea.files["clients/colegio/kustomization.yaml"]
    assert "colegio.hub.local" in gitea.files["clients/colegio/kustomization.yaml"]
    assert all(c["message"] == "feat(colegio): alta del sitio de Colegio San Marcos" for c in gitea.commits)


def test_un_sitio_solo_landing_escribe_un_archivo(client, seeded, gitea):
    servicio = _crear_sitio(client, "landing")
    assert client.post(f"/api/services/{servicio['id']}/provision").status_code == 201
    assert set(gitea.files) == {"clients/colegio/kustomization.yaml", "clients/colegio/catalog-info.yaml"}


def test_dar_de_alta_dos_veces_responde_409_y_no_escribe(client, seeded, gitea):
    servicio = _crear_sitio(client)
    client.post(f"/api/services/{servicio['id']}/provision")
    commits = len(gitea.commits)
    assert client.post(f"/api/services/{servicio['id']}/provision").status_code == 409
    assert len(gitea.commits) == commits


def test_sin_la_imagen_publicada_no_se_escribe_nada(client, seeded, gitea):
    gitea.images = {"colegio-web:v1"}   # falta colegio-api
    servicio = _crear_sitio(client)
    respuesta = client.post(f"/api/services/{servicio['id']}/provision")
    assert respuesta.status_code == 422
    assert "colegio-api:v1" in respuesta.json()["detail"]
    assert gitea.files == {} and gitea.commits == []


def test_el_alta_queda_en_la_bitacora(client, seeded, gitea):
    servicio = _crear_sitio(client)
    client.post(f"/api/services/{servicio['id']}/provision")
    registros = client.get("/api/audit-logs?entity=service&action=aprovisionar").json()
    assert any(r["entity_id"] == servicio["id"] for r in registros)


def test_un_servicio_inexistente_responde_404(client, seeded, gitea):
    assert client.post("/api/services/9999/provision").status_code == 404


def test_un_cliente_no_puede_dar_de_alta_sitios(as_client, seeded, gitea):
    assert as_client.post("/api/services/1/provision").status_code == 403
