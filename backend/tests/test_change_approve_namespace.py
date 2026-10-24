# Aprobar con un namespace que no es de un cliente no debe escribir en Gitea (spec 005).
from sqlalchemy import select

from app.models import Service
from tests.test_change_approve import cambio, gitea, tecnico  # noqa: F401  (fixtures compartidos)
import pytest


@pytest.fixture
def client(seeded, as_user):
    """Estas pruebas operan como Sofía, técnica de la agencia sembrada (spec 007)."""
    return as_user("sofia@forjadigital.test")


def test_un_namespace_que_no_es_de_un_cliente_no_escribe_en_gitea(client, seeded, gitea, tecnico, cambio):  # noqa: F811
    # Dato mal guardado (por ejemplo, de antes de validar el formato): jamás debe armar una ruta rara
    service = seeded.scalar(select(Service).where(Service.namespace == "cliente-ferreteria"))
    service.namespace = "cliente-x/../../hub/api"
    seeded.commit()

    response = client.post(f"/api/change-requests/{cambio['id']}/approve")

    assert response.status_code == 422
    assert gitea.commits == []
    assert not any("hub/api" in path for _, path in gitea.requests)
