# Pruebas de aprobar una solicitud de cambio: un commit en hub-gitops y nada más (spec 005, T14 · CA-2).
import pytest
from sqlalchemy import select

from app.config import settings
from app.integrations.gitea import GiteaClient
from app.main import app
from app.models import Service, Ticket, TicketEvent, User
from app.routers.change_requests import get_gitea
from tests.fake_gitea import FakeGitea


def _kustomization(cliente: str, imagen: str = "") -> str:
    imagen = imagen or cliente
    return (
        f"# Cliente {cliente}\n"
        "apiVersion: kustomize.config.k8s.io/v1beta1\n"
        "kind: Kustomization\n"
        f"namespace: cliente-{cliente}\n"
        "images:\n"
        "  - name: gitea.hub.local/forja-digital/plantilla\n"
        f"    newName: gitea.hub.local/forja-digital/{imagen}\n"
        "    newTag: v1\n"
        "patches:\n"
        "  - target: { kind: Namespace }\n"
    )


ARCHIVOS = {
    "clients/restaurante/kustomization.yaml": _kustomization("restaurante"),
    "clients/ferreteria/kustomization.yaml": _kustomization("ferreteria"),
    "clients/consultorio/kustomization.yaml": _kustomization("consultorio", "consultorio-web"),
}


@pytest.fixture
def gitea():
    with FakeGitea(ARCHIVOS) as fake:
        app.dependency_overrides[get_gitea] = lambda: GiteaClient(fake.url, fake.repo, fake.token)
        yield fake
        app.dependency_overrides.pop(get_gitea, None)


@pytest.fixture
def tecnico(seeded) -> User:
    return seeded.scalar(select(User).where(User.role == "agencia"))


@pytest.fixture
def cambio(client, seeded):
    """Una solicitud de cambio pendiente de El Tornillo (v1 → v1.1)."""
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    ticket = client.post(
        "/api/tickets",
        json={
            "service_id": service.id,
            "title": "Publicar la nueva portada",
            "description": "Portada de temporada.",
            "kind": "cambio",
        },
    ).json()
    created = client.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": "v1.1"})
    return created.json()


def test_aprobar_crea_exactamente_un_commit_y_no_toca_otros_archivos(client, gitea, tecnico, cambio):
    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 200
    assert len(gitea.commits) == 1
    commit = gitea.commits[0]
    assert commit["path"] == "clients/ferreteria/kustomization.yaml"
    assert commit["message"] == f"chore(ferreteria): versión v1.1 (cambio #{cambio['id']})"
    assert commit["author"] == {"name": tecnico.name, "email": tecnico.email}
    # Los otros dos clientes quedan idénticos y el de la ferretería solo cambia el tag
    assert gitea.files["clients/restaurante/kustomization.yaml"] == ARCHIVOS["clients/restaurante/kustomization.yaml"]
    assert gitea.files["clients/consultorio/kustomization.yaml"] == ARCHIVOS["clients/consultorio/kustomization.yaml"]
    assert gitea.files["clients/ferreteria/kustomization.yaml"] == ARCHIVOS[
        "clients/ferreteria/kustomization.yaml"
    ].replace("newTag: v1\n", "newTag: v1.1\n")


def test_deja_la_solicitud_en_validacion_con_el_sha_y_quien_aprobo(client, gitea, tecnico, cambio):
    body = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id}).json()

    assert body["status"] == "en_validacion"
    assert body["gitops_commit_sha"] == gitea.commits[0]["sha"]
    assert body["approved_by_id"] == tecnico.id
    assert body["approved_at"] is not None and body["deployed_at"] is None


def test_cada_paso_deja_hora_y_usuario_en_el_historial(client, seeded, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    events = seeded.scalars(
        select(TicketEvent).where(TicketEvent.ticket_id == cambio["ticket_id"], TicketEvent.type == "cambio")
        .order_by(TicketEvent.id)
    ).all()
    assert [(e.from_value, e.to_value) for e in events] == [
        (None, "pendiente"),
        ("pendiente", "aprobada"),
        ("aprobada", "en_validacion"),
    ]
    assert all(e.created_at is not None for e in events)
    assert [e.actor_id for e in events[1:]] == [tecnico.id, tecnico.id]


def test_si_gitea_falla_la_solicitud_sigue_pendiente(client, gitea, tecnico, cambio):
    # El Hub tiene un token que Gitea no reconoce (401)
    app.dependency_overrides[get_gitea] = lambda: GiteaClient(gitea.url, gitea.repo, "token-equivocado")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 502
    assert "Gitea" in response.json()["detail"]
    assert gitea.commits == []
    # nada cambió: con el token correcto se puede reintentar
    app.dependency_overrides[get_gitea] = lambda: GiteaClient(gitea.url, gitea.repo, gitea.token)
    retry = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})
    assert retry.status_code == 200 and len(gitea.commits) == 1


def test_no_se_aprueba_dos_veces(client, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    again = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert again.status_code == 409
    assert len(gitea.commits) == 1


def test_un_cambio_rechazado_no_se_aprueba(client, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/reject", json={"reason": "No aplica"})

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 409
    assert gitea.commits == []


def test_un_usuario_cliente_no_puede_aprobar(client, seeded, gitea, cambio):
    usuario_cliente = seeded.scalar(select(User).where(User.role == "cliente"))

    response = client.post(
        f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": usuario_cliente.id}
    )

    assert response.status_code == 403
    assert gitea.commits == []


def test_exige_quien_aprueba(client, gitea, cambio):
    missing = client.post(f"/api/change-requests/{cambio['id']}/approve", json={})
    unknown = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": 9999})

    assert missing.status_code == 422
    assert unknown.status_code == 404


def test_si_el_repo_ya_tiene_la_version_no_hace_commit(client, gitea, tecnico, cambio):
    gitea.files["clients/ferreteria/kustomization.yaml"] = ARCHIVOS[
        "clients/ferreteria/kustomization.yaml"
    ].replace("newTag: v1\n", "newTag: v1.1\n")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 409
    assert gitea.commits == []


def test_sin_configurar_gitea_responde_503(client, tecnico, cambio, monkeypatch):
    # No depende del entorno: aunque el contenedor tenga GITEA_URL y GITEA_TOKEN, aquí van vacíos
    monkeypatch.setattr(settings, "gitea_url", "")
    monkeypatch.setattr(settings, "gitea_token", "")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 503
    assert "GITEA_URL" in response.json()["detail"]


# ---------- Aprobación que escribió en Gitea pero no alcanzó a guardarse ----------

def _publicacion_previa(gitea, cambio, mensaje=None):
    """Deja en Gitea el commit que habría hecho la aprobación, como si la base hubiera fallado después."""
    cliente = GiteaClient(gitea.url, gitea.repo, gitea.token)
    archivo = cliente.get_file("clients/ferreteria/kustomization.yaml")
    return cliente.update_file(
        "clients/ferreteria/kustomization.yaml",
        archivo.text.replace("newTag: v1" + chr(10), "newTag: v1.1" + chr(10)),
        archivo.sha,
        mensaje or f"chore(ferreteria): versión v1.1 (cambio #{cambio['id']})",
        "Sofía", "sofia@forjadigital.test",
    )


def test_adopta_el_commit_si_la_aprobacion_anterior_no_alcanzo_a_guardarse(client, gitea, tecnico, cambio):
    sha = _publicacion_previa(gitea, cambio)

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 200
    assert response.json()["status"] == "en_validacion"
    assert response.json()["gitops_commit_sha"] == sha
    assert len(gitea.commits) == 1  # no se hizo un segundo commit


def test_si_el_ultimo_commit_no_es_de_este_cambio_sigue_siendo_409(client, gitea, tecnico, cambio):
    _publicacion_previa(gitea, cambio, mensaje="chore(ferreteria): versión v1.1 (cambio #999)")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})

    assert response.status_code == 409


def test_el_cliente_no_ve_jerga_en_el_historial_del_cambio(client, seeded, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": tecnico.id})
    ticket = seeded.get(Ticket, cambio["ticket_id"])
    client_id = ticket.service.project.client_id

    vista = client.get(
        f"/api/tickets/{ticket.id}", params={"viewer_role": "cliente", "client_id": client_id}
    ).json()

    cambios = [e for e in vista["events"] if e["type"] == "cambio"]
    assert [(e["from_value"], e["to_value"]) for e in cambios] == [(None, "Pendiente"), ("Pendiente", "Aprobada")]
    texto = " ".join(str(e) for e in cambios).lower()
    for jerga in ("commit", "hub-gitops", "argo", "en_validacion"):
        assert jerga not in texto
    # la agencia sí ve el paso técnico
    agencia = client.get(f"/api/tickets/{ticket.id}").json()
    assert any("hub-gitops" in (e["note"] or "") for e in agencia["events"])
