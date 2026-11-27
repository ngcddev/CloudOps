# Alertas de la plataforma (spec 022, T10; auditoría OB-01, OB-02 y OB-03): ninguna puede acabar en el webhook del Hub (abriría incidentes de sitio por
# algo que no es un sitio, y HubCaido no puede avisar a quien está caído), y el monitoreo sondea el Hub en un job aparte de los sitios.
from pathlib import Path

import pytest
import yaml

REPO = Path("/repo")
OBS = REPO / "observability"

pytestmark = pytest.mark.skipif(not OBS.exists(), reason="el repositorio no está montado en /repo")

ESPERADAS = {"HubCaido", "MonitoreoCiego", "Watchdog", "ContenedorSinMemoria", "ContenedorEnBucle", "NodoSinMemoria", "DiscoDelNodoLleno", "RespaldoDelHubSinExito"}


def _cargar(ruta: str) -> dict:
    return yaml.safe_load((OBS / ruta).read_text(encoding="utf-8"))


def _alertas_de_plataforma() -> list[dict]:
    return [r for g in _cargar("prometheus/reglas/plataforma.yml")["groups"] for r in g["rules"] if "alert" in r]


def test_estan_las_alertas_de_la_plataforma():
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


# --- OB-03, OB-04 y OB-05 (spec 022, T25 y T26) ---


def test_prometheus_recoge_el_nodo_los_volumenes_y_el_estado_de_los_cronjobs():
    trabajos = {j["job_name"]: j for j in _cargar("prometheus/prometheus.yml")["scrape_configs"]}
    assert {"cadvisor", "kubelet", "kube-state-metrics"} <= set(trabajos)
    assert "kubelet_volume_stats" in trabajos["kubelet"]["metric_relabel_configs"][0]["regex"]
    assert trabajos["kube-state-metrics"]["static_configs"][0]["targets"] == ["kube-state-metrics.monitoring.svc:8080"]
    # cAdvisor ya no descarta las series del nodo entero (id="/"): sin ellas no hay NodoSinMemoria
    regex = trabajos["cadvisor"]["metric_relabel_configs"][0]["regex"]
    assert "machine_memory_bytes" in regex and "container_memory_working_set_bytes" in regex


def test_kube_state_metrics_solo_lee_cronjobs_y_jobs_y_corre_sin_privilegios():
    docs = list(yaml.safe_load_all((OBS / "kube-state-metrics/deployment.yaml").read_text(encoding="utf-8")))
    rol = next(d for d in docs if d["kind"] == "ClusterRole")
    assert rol["rules"] == [{"apiGroups": ["batch"], "resources": ["cronjobs", "jobs"], "verbs": ["list", "watch"]}]   # nada de secretos ni de escritura
    despliegue = next(d for d in docs if d["kind"] == "Deployment")
    contenedor = despliegue["spec"]["template"]["spec"]["containers"][0]
    assert "--resources=cronjobs,jobs" in contenedor["args"]
    assert contenedor["securityContext"]["readOnlyRootFilesystem"] is True and contenedor["securityContext"]["capabilities"] == {"drop": ["ALL"]}
    assert contenedor["resources"]["limits"]["memory"] == "64Mi"
    assert "kube-state-metrics" in _cargar("kustomization.yaml")["resources"]


def test_ninguna_alerta_que_no_notifica_a_nadie_se_llama_critica():
    # Alertmanager manda estas rutas a `solo-ver`, que no avisa a nadie: una etiqueta `critical` ahí engaña (auditoría OB-05)
    reglas = [r for g in _cargar("prometheus/reglas/presupuesto.yml")["groups"] for r in g["rules"] if "alert" in r]
    assert {r["alert"] for r in reglas} == {"PresupuestoQuemadoRapido", "PresupuestoQuemadoLento"}
    assert all(r["labels"]["severity"] == "warning" and "priority" not in r["labels"] for r in reglas)
    assert not [r["alert"] for r in _alertas_de_plataforma() if r["labels"]["severity"] == "critical" and r["alert"] not in {"HubCaido", "MonitoreoCiego"}]


def test_alloy_recoge_el_hub_pero_no_postgres_ni_el_respaldo():
    configuracion = (OBS / "alloy/config.alloy").read_text(encoding="utf-8")
    assert 'regex         = "cliente-.+|hub"' in configuracion
    assert 'regex         = "postgres|hub-db-backup"' in configuracion and 'action        = "drop"' in configuracion


def test_grafana_enlaza_loki_y_tempo_por_el_trace_id():
    fuentes = {f["uid"]: f for f in _cargar("grafana/datasources.yaml")["datasources"]}
    campo = fuentes["loki"]["jsonData"]["derivedFields"][0]
    assert campo["datasourceUid"] == "tempo" and "trace_id" in campo["matcherRegex"] and campo["url"].endswith("{__value.raw}")
    traza_a_registros = fuentes["tempo"]["jsonData"]["tracesToLogsV2"]
    assert traza_a_registros["datasourceUid"] == "loki" and '{namespace="hub"}' in traza_a_registros["query"]
