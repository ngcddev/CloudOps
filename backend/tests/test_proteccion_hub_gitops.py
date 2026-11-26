# La protección de hub-gitops en Gitea (spec 022, T13; auditoría K8-05) deja a `hub-bot` cambiar solo lo que el Hub escribe. Esta prueba ata esa regla al código:
# todas las rutas que el Hub escribe de verdad (alta de un sitio, versión, rollback) coinciden con los patrones permitidos, y lo que escribe el equipo no.
# Si el Hub empieza a escribir en otra ruta, esta prueba falla antes de que Gitea le responda 403 en el clúster. La regla misma se prueba contra Gitea con
# gitops/pruebas/proteccion_hub_gitops.py.
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Service
from app.services import gitops_publish, provisioning

MODULO = Path("/repo/gitops/proteccion_hub_gitops.py")
pytestmark = pytest.mark.skipif(not MODULO.exists(), reason="el repositorio no está montado en /repo")


@pytest.fixture(scope="module")
def proteccion():
    especificacion = importlib.util.spec_from_file_location("proteccion_hub_gitops", MODULO)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def test_lo_que_el_hub_escribe_esta_permitido(seeded, proteccion):
    escritas = set()
    for servicio in seeded.scalars(select(Service)):
        escritas |= set(provisioning.render_files(servicio, servicio.plan))       # alta de un sitio: kustomization, catalog-info y backend
        escritas.add(gitops_publish.kustomization_path(servicio.namespace))        # versión nueva y rollback
    assert escritas and any(ruta.endswith("backend.yaml") for ruta in escritas), "se esperaban los tres archivos de un sitio con formulario"

    no_permitidas = sorted(ruta for ruta in escritas if not proteccion.hub_can_change(ruta))
    assert not no_permitidas, f"el Hub escribe rutas que la protección de Gitea le bloquearía: {no_permitidas}"


@pytest.mark.parametrize("ruta", [
    "observability/prometheus/prometheus.yml", "observability/prometheus/reglas/plataforma.yml", "hub/api.yaml", "hub/escalado.yaml",
    "platform/backstage/deployment.yaml", "clients/_base/deployment.yaml", "clients/_base/networkpolicy.yaml",
    "clients/ferreteria/otro.yaml", "clients/a/b/kustomization.yaml", "kustomization.yaml",
])
def test_lo_que_escribe_el_equipo_sigue_protegido(ruta, proteccion):
    assert not proteccion.hub_can_change(ruta)


def test_la_regla_deja_empujar_solo_al_administrador(proteccion):
    regla = proteccion.rule("forja-admin")
    assert regla["push_whitelist_usernames"] == ["forja-admin"] and regla["enable_push_whitelist"] is True
    assert regla["unprotected_file_patterns"] == ";".join(proteccion.HUB_PATTERNS)
    assert "protected_file_patterns" not in regla   # se usa la lista de lo permitido, no la de lo prohibido: lo nuevo nace protegido


def test_diferencias_detecta_una_regla_que_no_es_la_esperada(proteccion):
    esperada = proteccion.rule("forja-admin")
    assert proteccion.differences(dict(esperada), esperada) == []
    suelta = {**esperada, "enable_push_whitelist": False, "unprotected_file_patterns": "", "push_whitelist_usernames": ["hub-bot"]}
    campos = " ".join(proteccion.differences(suelta, esperada))
    assert "enable_push_whitelist" in campos and "unprotected_file_patterns" in campos and "push_whitelist_usernames" in campos


def test_el_glob_se_comporta_como_el_de_gitea(proteccion):
    assert proteccion.matches("clients/*/kustomization.yaml", "clients/ferreteria/kustomization.yaml")
    assert not proteccion.matches("clients/*/kustomization.yaml", "clients/a/b/kustomization.yaml")   # `*` no cruza carpetas
    assert proteccion.matches("observability/**", "observability/a/b/c.yml")                           # `**` sí
