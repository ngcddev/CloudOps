# La API de desarrollo no monta la raíz del repositorio (spec 022, T28; auditoría CT-02): ahí viven `.env` y `.env.cluster`, con los secretos del entorno y de la
# demo, y el proceso que recibe tráfico no debe poder leerlos. Las pruebas solo necesitan unas carpetas concretas de solo lectura.
from pathlib import Path

import pytest
import yaml

COMPOSE = Path("/repo/docker-compose.yml")

pytestmark = pytest.mark.skipif(not COMPOSE.exists(), reason="docker-compose.yml no está montado en /repo")


def _montajes(servicio: str) -> list[str]:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"][servicio].get("volumes", [])


def test_la_api_no_monta_la_raiz_del_repositorio():
    for montaje in _montajes("api"):
        origen = str(montaje).split(":")[0] if isinstance(montaje, str) else montaje.get("source", "")
        assert origen.rstrip("/") not in {".", "./", ""}, f"la API monta la raíz del repositorio ({montaje}): ahí están .env y .env.cluster"
        assert ".env" not in origen, f"la API monta un archivo de secretos ({montaje})"


def test_todo_lo_que_monta_la_api_es_de_solo_lectura():
    montajes = [m for m in _montajes("api") if isinstance(m, str) and m.split(":")[0].startswith("./")]
    assert montajes and all(m.endswith(":ro") for m in montajes), [m for m in montajes if not m.endswith(":ro")]


def test_los_montajes_cubren_lo_que_leen_las_pruebas_de_runbooks_y_alertas():
    destinos = {str(m).split(":")[1] for m in _montajes("api") if isinstance(m, str) and m.startswith("./")}
    assert {"/repo/docs", "/repo/runbooks", "/repo/observability", "/repo/voz", "/repo/gitops", "/repo/backend"} <= destinos


# --- CT-04: MLflow y el endpoint de la compuerta solo en esta máquina ---

MLFLOW = Path("/repo/ai/servidor-mlflow/docker-compose.yml")


@pytest.mark.skipif(not MLFLOW.exists(), reason="ai/ no está montado en /repo")
def test_mlflow_y_la_compuerta_se_publican_en_loopback_por_defecto():
    servicios = yaml.safe_load(MLFLOW.read_text(encoding="utf-8"))["services"]
    for nombre in ("mlflow", "modelo-compuerta"):
        for puerto in servicios[nombre]["ports"]:
            # Sin autenticación (auditoría CT-04): el valor por defecto de la dirección es 127.0.0.1; solo MLFLOW_BIND lo abre
            assert str(puerto).startswith("${MLFLOW_BIND:-127.0.0.1}:"), f"{nombre} publica {puerto} en todas las interfaces"


# --- CT-03: el runner, una excepción conocida, endurecida ---

RUNNER = Path("/repo/pipelines/runner/docker-compose.yml")


@pytest.mark.skipif(not RUNNER.exists(), reason="pipelines/ no está montado en /repo")
def test_el_runner_no_tiene_capacidades_ni_puede_ganar_privilegios():
    runner = yaml.safe_load(RUNNER.read_text(encoding="utf-8"))["services"]["runner"]
    assert runner.get("cap_drop") == ["ALL"] and "cap_add" not in runner
    assert "no-new-privileges:true" in runner.get("security_opt", [])
    assert runner.get("mem_limit") and runner.get("cpus")   # los límites que ya tenía siguen
    assert runner.get("privileged") is not True
