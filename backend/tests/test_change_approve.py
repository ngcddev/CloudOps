# Pruebas de aprobar una solicitud de cambio: un commit en hub-gitops y nada más (spec 005, T14 · CA-2).
import pytest
from sqlalchemy import select

from app.config import settings
from app.integrations.gitea import GiteaClient
from app.main import app
from app.models import AuditLog, Service, Ticket, TicketEvent, User
from app.routers.change_requests import get_gitea
from tests.fake_gitea import FakeGitea


@pytest.fixture
def client(seeded, as_user):
    """Estas pruebas operan como Sofía, técnica de la agencia sembrada (spec 007)."""
    return as_user("sofia@forjadigital.test")


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
def cambio(client, seeded, pass_gate):
    """Una solicitud de cambio pendiente de El Tornillo (v1 → v1.1), con su versión ya revisada por la puerta."""
    pass_gate("cliente-ferreteria", "v1.1")
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
    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

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
    body = client.post(f"/api/change-requests/{cambio['id']}/approve").json()

    assert body["status"] == "en_validacion"
    assert body["gitops_commit_sha"] == gitea.commits[0]["sha"]
    assert body["approved_by_id"] == tecnico.id
    assert body["approved_at"] is not None and body["deployed_at"] is None


def test_cada_paso_deja_hora_y_usuario_en_el_historial(client, seeded, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve")

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

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 502
    assert "Gitea" in response.json()["detail"]
    assert gitea.commits == []
    # nada cambió: con el token correcto se puede reintentar
    app.dependency_overrides[get_gitea] = lambda: GiteaClient(gitea.url, gitea.repo, gitea.token)
    retry = client.post(f"/api/change-requests/{cambio['id']}/approve")
    assert retry.status_code == 200 and len(gitea.commits) == 1


def test_no_se_aprueba_dos_veces(client, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve")

    again = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert again.status_code == 409
    assert len(gitea.commits) == 1


def test_un_cambio_rechazado_no_se_aprueba(client, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/reject", json={"reason": "No aplica"})

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 409
    assert gitea.commits == []


def test_un_usuario_cliente_no_puede_aprobar(as_user, seeded, gitea, cambio):
    response = as_user("contacto@eltornillo.test").post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 403
    assert gitea.commits == []


def test_sin_sesion_no_se_puede_aprobar(anonymous, gitea, cambio):
    response = anonymous.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 401
    assert gitea.commits == []


def test_quien_aprueba_es_el_usuario_de_la_sesion_aunque_el_cuerpo_diga_otro(as_user, seeded, gitea, cambio):
    otro = seeded.scalar(select(User).where(User.email == "camilo@forjadigital.test"))
    sofia = seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))

    body = as_user("sofia@forjadigital.test").post(
        f"/api/change-requests/{cambio['id']}/approve", json={"actor_id": otro.id}
    ).json()

    assert body["approved_by_id"] == sofia.id
    assert gitea.commits[0]["author"] == {"name": sofia.name, "email": sofia.email}


def test_si_el_repo_ya_tiene_la_version_no_hace_commit(client, gitea, tecnico, cambio):
    gitea.files["clients/ferreteria/kustomization.yaml"] = ARCHIVOS[
        "clients/ferreteria/kustomization.yaml"
    ].replace("newTag: v1\n", "newTag: v1.1\n")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 409
    assert gitea.commits == []


def test_sin_configurar_gitea_responde_503(client, tecnico, cambio, monkeypatch):
    # No depende del entorno: aunque el contenedor tenga GITEA_URL y GITEA_TOKEN, aquí van vacíos
    monkeypatch.setattr(settings, "gitea_url", "")
    monkeypatch.setattr(settings, "gitea_token", "")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

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

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "en_validacion"
    assert response.json()["gitops_commit_sha"] == sha
    assert len(gitea.commits) == 1  # no se hizo un segundo commit


def test_si_el_ultimo_commit_no_es_de_este_cambio_sigue_siendo_409(client, gitea, tecnico, cambio):
    _publicacion_previa(gitea, cambio, mensaje="chore(ferreteria): versión v1.1 (cambio #999)")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 409


def test_el_cliente_no_ve_jerga_en_el_historial_del_cambio(client, as_user, seeded, gitea, tecnico, cambio):
    client.post(f"/api/change-requests/{cambio['id']}/approve")
    ticket = seeded.get(Ticket, cambio["ticket_id"])
    client_id = ticket.service.project.client_id

    dueno = seeded.scalar(select(User).where(User.client_id == client_id))
    vista = as_user(dueno.email).get(f"/api/tickets/{ticket.id}").json()

    cambios = [e for e in vista["events"] if e["type"] == "cambio"]
    assert [(e["from_value"], e["to_value"]) for e in cambios] == [(None, "Pendiente"), ("Pendiente", "Aprobada")]
    texto = " ".join(str(e) for e in cambios).lower()
    for jerga in ("commit", "hub-gitops", "argo", "en_validacion"):
        assert jerga not in texto
    # la agencia sí ve el paso técnico
    agencia = client.get(f"/api/tickets/{ticket.id}").json()
    assert any("hub-gitops" in (e["note"] or "") for e in agencia["events"])


def test_aprobar_queda_en_la_bitacora_con_la_version_y_el_commit(client, seeded, gitea, cambio):
    sofia = seeded.scalar(select(User).where(User.email == "sofia@forjadigital.test"))
    body = client.post(f"/api/change-requests/{cambio['id']}/approve").json()

    logs = seeded.scalars(
        select(AuditLog).where(AuditLog.entity == "change_request", AuditLog.action == "aprobar")
    ).all()
    assert [(log.user_id, log.entity_id) for log in logs] == [(sofia.id, cambio["id"])]
    assert logs[0].details == {"a": "v1.1", "commit": body["gitops_commit_sha"][:7]}


def test_si_gitea_falla_no_queda_fila_de_aprobacion_en_la_bitacora(client, seeded, gitea, cambio):
    app.dependency_overrides[get_gitea] = lambda: GiteaClient(gitea.url, gitea.repo, "token-equivocado")

    assert client.post(f"/api/change-requests/{cambio['id']}/approve").status_code == 502

    assert seeded.scalars(select(AuditLog).where(AuditLog.action == "aprobar")).all() == []


# --- Puerta de seguridad (spec 006, T15 · CA-6) ---


def _pedir(client, seeded, version):
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    ticket = client.post(
        "/api/tickets",
        json={"service_id": service.id, "title": "Publicar", "description": "x", "kind": "cambio"},
    ).json()
    return client.post("/api/change-requests", json={"ticket_id": ticket["id"], "to_version": version}).json()


def test_sin_corrida_no_se_puede_aprobar_y_gitea_no_recibe_nada(client, seeded, gitea):
    cambio = _pedir(client, seeded, "v1.1")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 409
    assert "aún no pasó por la puerta de seguridad" in response.json()["detail"]
    assert gitea.commits == []
    assert client.get("/api/change-requests").json()[0]["status"] == "pendiente"


def test_con_la_corrida_en_curso_no_se_puede_aprobar(client, seeded, gitea):
    from app.services import security_gate as gate

    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    gate.open_run(seeded, service.id, "v1.1", None, ["ferreteria"])
    seeded.commit()
    cambio = _pedir(client, seeded, "v1.1")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 409
    assert "todavía están corriendo" in response.json()["detail"]
    assert gitea.commits == []


def test_con_la_corrida_fallida_el_motivo_dice_que_control_fallo(client, seeded, gitea):
    from app.services import security_gate as gate

    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    run = gate.open_run(seeded, service.id, "v1.1", None, ["ferreteria"])
    gate.add_check(seeded, run, "secretos", "ok", "", None, None)
    gate.add_check(seeded, run, "vulnerabilidades", "fallo", "2 críticas", None, "ferreteria")
    seeded.commit()
    # el cambio se pide a mano en la base: pedirlo por la API ya lo rechaza solo
    from app.models import ChangeRequest, Ticket

    ticket = Ticket(service_id=service.id, title="Publicar", description="x", kind="cambio")
    seeded.add(ticket)
    seeded.flush()
    change = ChangeRequest(ticket_id=ticket.id, service_id=service.id, from_version="v1", to_version="v1.1", status="pendiente")
    seeded.add(change)
    seeded.commit()

    response = client.post(f"/api/change-requests/{change.id}/approve")

    assert response.status_code == 409
    assert "vulnerabilidades críticas" in response.json()["detail"]
    assert gitea.commits == []


def test_la_puerta_de_otra_version_no_sirve(client, seeded, gitea, pass_gate):
    pass_gate("cliente-ferreteria", "v1.2")
    cambio = _pedir(client, seeded, "v1.1")

    assert client.post(f"/api/change-requests/{cambio['id']}/approve").status_code == 409


def test_con_la_puerta_en_ok_se_publica_como_antes(client, seeded, gitea, pass_gate):
    pass_gate("cliente-ferreteria", "v1.1")
    cambio = _pedir(client, seeded, "v1.1")

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 200
    assert len(gitea.commits) == 1
