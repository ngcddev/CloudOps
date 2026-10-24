# Validación del workflow y los scripts de la puerta de seguridad (spec 006, T08-T11).
# No ejecuta el pipeline (eso lo hacen pipelines/pruebas/simular-puerta.sh y el runner): comprueba que el workflow
# y los scripts no se desalineen y que ningún secreto quede escrito en ellos (RNF-06).
import re
from pathlib import Path

import pytest
import yaml

PIPELINES = Path(__file__).resolve().parents[2] / "pipelines"


def _leer(nombre: str) -> str:
    path = PIPELINES / nombre
    if not path.exists():
        pytest.skip("pipelines/ no está en esta imagen; corre en el repo completo")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def workflow() -> dict:
    return yaml.safe_load(_leer("puerta.yaml"))


def _pasos(workflow: dict) -> list[dict]:
    return workflow["jobs"]["puerta"]["steps"]


def test_corre_al_subir_una_etiqueta_de_version(workflow):
    # PyYAML lee la clave `on` como True
    disparador = workflow.get("on", workflow.get(True))

    assert disparador == {"push": {"tags": ["v*"]}}


def test_los_pasos_van_en_el_orden_de_la_puerta(workflow):
    llamadas = []
    for paso in _pasos(workflow)[1:]:  # el primero descarga la versión
        match = re.search(r'bash "\$PUERTA" (\w+)', paso["run"])
        assert match, f"El paso «{paso['name']}» no llama a puerta.sh"
        llamadas.append(match.group(1))

    assert llamadas == ["inicio", "secretos", "construir", "vulnerabilidades", "sbom", "firmar", "verificar", "fin"]


def test_cada_paso_del_workflow_existe_en_puerta_sh(workflow):
    script = _leer("puerta.sh")
    for paso in _pasos(workflow)[1:]:
        nombre = re.search(r'bash "\$PUERTA" (\w+)', paso["run"]).group(1)
        assert re.search(rf"^  {nombre}\)", script, re.MULTILINE), f"puerta.sh no tiene el paso «{nombre}»"


def test_el_cierre_corre_siempre_y_conoce_el_resultado_del_trabajo(workflow):
    cierre = _pasos(workflow)[-1]

    assert "always()" in str(cierre["if"])
    assert cierre["env"]["JOB_STATUS"] == "${{ job.status }}"


def test_los_secretos_salen_de_gitea_y_ninguno_esta_escrito(workflow):
    texto = _leer("puerta.yaml")
    valores = [v for paso in _pasos(workflow) for v in paso.get("env", {}).values()]
    valores += list(workflow["jobs"]["puerta"]["env"].values())

    for nombre in ("HUB_PIPELINE_TOKEN", "REGISTRY_PASSWORD", "COSIGN_PRIVATE_KEY", "COSIGN_PASSWORD", "HUB_URL"):
        assert f"${{{{ secrets.{nombre} }}}}" in texto
    # todo valor del entorno es una expresión de Gitea ($\{{ ... }}) o una ruta fija, nunca un literal con aspecto de clave
    for valor in valores:
        assert str(valor).startswith("${{") or str(valor) == ".gitea/puerta/puerta.sh"


def test_la_clave_de_firma_solo_llega_a_los_pasos_que_la_usan(workflow):
    con_clave = [p["name"] for p in _pasos(workflow) if "COSIGN_PRIVATE_KEY" in p.get("env", {})]

    assert con_clave == ["Subir y firmar (Cosign)"]


def test_los_scripts_fijan_la_version_de_cada_herramienta():
    lib = _leer("lib.sh")

    for herramienta in ("GITLEAKS_IMAGE", "TRIVY_IMAGE", "SYFT_IMAGE", "COSIGN_IMAGE", "SKOPEO_IMAGE", "JQ_IMAGE"):
        linea = next(l for l in lib.splitlines() if l.startswith(f"{herramienta}="))
        etiqueta = linea.split(":-")[1].rstrip('}"').rsplit(":", 1)[1]
        assert etiqueta not in ("latest", "stable"), f"{herramienta} usa una etiqueta móvil"


def test_ningun_script_guarda_una_clave_privada_ni_un_token():
    for nombre in ("puerta.sh", "reportar.sh", "lib.sh", "puerta.yaml", "configurar-gitea.sh", "sembrar-repos-sitios.sh"):
        texto = _leer(nombre)
        assert "BEGIN ENCRYPTED SIGSTORE PRIVATE KEY" not in texto
        assert "BEGIN PRIVATE KEY" not in texto
        assert not re.search(r"(?i)(token|password)\s*=\s*['\"][A-Za-z0-9]{16,}['\"]", texto), nombre
