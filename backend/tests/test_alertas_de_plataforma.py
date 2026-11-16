# Alertas de la plataforma (spec 022, T10; auditoría OB-01, OB-02 y OB-03): ninguna puede acabar en el webhook del Hub (abriría incidentes de sitio por
# algo que no es un sitio, y HubCaido no puede avisar a quien está caído), y el monitoreo sondea el Hub en un job aparte de los sitios.
from pathlib import Path

import pytest
import yaml

REPO = Path("/repo")
OBS = REPO / "observability"

pytestmark = pytest.mark.skipif(not OBS.exists(), reason="el repositorio no está montado en /repo")

ESPERADAS = {"HubCaido", "MonitoreoCiego", "Watchdog", "ContenedorSinMemoria", "ContenedorEnBucle"}


def _cargar(ruta: str) -> dict:
    return yaml.safe_load((OBS / ruta).read_text(encoding="utf-8"))


def _alertas_de_plataforma() -> list[dict]:
    return [r for g in _cargar("prometheus/reglas/plataforma.yml")["groups"] for r in g["rules"] if "alert" in r]


def test_estan_las_cinco_alertas_de_la_plataforma():
    assert {r["alert"] for r in _alertas_de_plataforma()} == ESPERADAS


def test_toda_alerta_de_plataforma_lleva_destino_plataforma():
    sin_destino = [r["alert"] for r in _alertas_de_plataforma() if r.get("labels", {}).get("destino") != "plataforma"]
    assert not sin_destino, f"estas alertas irían al Hub: {sin_destino}"


def test_alertmanager_manda_destino_plataforma_a_solo_ver_y_el_resto_sigue_al_hub():
    config = _cargar("alertmanager/alertmanager.yml")
    assert config["route"]["receiver"] == "hub"   # por defecto, todo va al Hub
    rutas = {tuple(sorted(r["matchers"])): r["receiver"] for r in config["route"]["routes"]}
    assert rutas[('destino = "plataforma"',)] == "solo-ver"
    # SitioCaido no tiene ruta propia: sigue por la ruta por defecto, hacia el Hub
    assert not any("SitioCaido" in m for matchers in rutas for m in matchers)


def test_prometheus_sondea_el_hub_en_un_job_aparte_de_los_sitios():
    trabajos = {j["job_name"]: j for j in _cargar("prometheus/prometheus.yml")["scrape_configs"]}
    hub = trabajos["hub"]
    objetivos = hub["static_configs"][0]["targets"]
    assert "http://api.hub.svc.cluster.local:8000/health" in objetivos   # /health, no /livez: sin base el Hub no está sano
    assert any(o.startswith("http://web.hub.svc.cluster.local") for o in objetivos)
    assert hub["scrape_timeout"] != hub["scrape_interval"] and hub["params"]["module"] == ["http_2xx"]
    # SitioCaido (que abre incidentes en el Hub) sigue leyendo solo el job de los sitios
    regla = yaml.safe_load((OBS / "prometheus/reglas/sitios.yml").read_text(encoding="utf-8"))["groups"][0]["rules"][0]
    assert regla["alert"] == "SitioCaido" and 'job="sitios"' in regla["expr"]


def test_las_reglas_de_la_plataforma_entran_al_configmap_de_prometheus():
    kustomization = _cargar("prometheus/kustomization.yaml")
    reglas = next(g for g in kustomization["configMapGenerator"] if g["name"] == "prometheus-reglas")
    assert "reglas/plataforma.yml" in reglas["files"]
