# Hallazgos menores de Kubernetes, observabilidad y herramientas (spec 022, T37): K8-08 a K8-10, K8-12, K8-13, K8-15, OB-07, OB-09, OB-10 y IA-02, IA-03, IA-05, IA-07, IA-08.
import re
from pathlib import Path

import pytest
import yaml

REPO = Path("/repo")
HUB = REPO / "gitops" / "hub"

pytestmark = pytest.mark.skipif(not HUB.exists(), reason="el repositorio no está montado en /repo")


def _docs(ruta: Path) -> list[dict]:
    return [d for d in yaml.safe_load_all(ruta.read_text(encoding="utf-8")) if d]


def _pod_spec(doc: dict) -> dict:
    plantilla = doc["spec"]["template"] if doc["kind"] != "CronJob" else doc["spec"]["jobTemplate"]["spec"]["template"]
    return plantilla["spec"]


def _cargas() -> dict[str, dict]:
    cargas = {}
    for archivo in ("api", "web", "postgres", "voz", "backup"):
        for doc in _docs(HUB / f"{archivo}.yaml"):
            if doc["kind"] in ("Deployment", "StatefulSet", "CronJob"):
                cargas[doc["metadata"]["name"]] = doc
    return cargas


# ---------- K8-08 y K8-15 ----------


@pytest.mark.parametrize("nombre", ["api", "web", "postgres", "hub-db-backup"])
def test_los_pods_del_hub_corren_con_la_raiz_de_solo_lectura_y_un_volumen_para_lo_que_escriben(nombre):
    spec = _pod_spec(_cargas()[nombre])
    contenedor = spec["containers"][0]
    assert contenedor["securityContext"]["readOnlyRootFilesystem"] is True
    montajes = {m["mountPath"] for m in contenedor["volumeMounts"]}
    assert "/tmp" in montajes   # sin un volumen vacío en /tmp nada de lo que escribe (pid, temporales) arrancaría
    plantillas = {c["metadata"]["name"] for c in _cargas()[nombre]["spec"].get("volumeClaimTemplates", [])}   # el volumen de datos de un StatefulSet
    volumenes = {v["name"] for v in spec["volumes"]} | plantillas
    assert {m["name"] for m in contenedor["volumeMounts"]} <= volumenes


def test_postgres_escribe_su_socket_en_un_volumen_vacio_y_sus_datos_en_su_volumen():
    contenedor = _pod_spec(_cargas()["postgres"])["containers"][0]
    montajes = {m["mountPath"] for m in contenedor["volumeMounts"]}
    assert {"/var/run/postgresql", "/var/lib/postgresql/data"} <= montajes


def test_cada_aplicacion_del_hub_tiene_su_serviceaccount_sin_token():
    cuentas = {d["metadata"]["name"]: d for d in _docs(HUB / "serviceaccounts.yaml") if d["kind"] == "ServiceAccount"}
    assert set(cuentas) == {"api", "web", "voz", "postgres", "hub-db-backup"}
    assert all(c["automountServiceAccountToken"] is False for c in cuentas.values())
    for nombre, doc in _cargas().items():
        spec = _pod_spec(doc)
        assert spec["serviceAccountName"] == nombre and spec["automountServiceAccountToken"] is False, nombre


def test_la_api_y_la_base_tienen_prioridad_alta():
    prioridades = [d for d in _docs(HUB / "serviceaccounts.yaml") if d["kind"] == "PriorityClass"]
    assert prioridades and prioridades[0]["metadata"]["name"] == "hub-critico" and prioridades[0]["globalDefault"] is False
    assert _pod_spec(_cargas()["api"])["priorityClassName"] == "hub-critico" and _pod_spec(_cargas()["postgres"])["priorityClassName"] == "hub-critico"
    kustomizacion = yaml.safe_load((HUB / "kustomization.yaml").read_text(encoding="utf-8"))["resources"]
    assert {"serviceaccounts.yaml", "limitrange.yaml"} <= set(kustomizacion)


# ---------- K8-09, K8-10, K8-12, K8-13 ----------


def test_los_namespaces_de_la_plataforma_avisan_de_pod_security_restricted():
    espacios = {d["metadata"]["name"]: d["metadata"].get("labels", {}) for d in _docs(REPO / "gitops/platform/namespaces.yaml")}
    for nombre in ("argocd", "monitoring", "gitea"):
        assert espacios[nombre]["pod-security.kubernetes.io/warn"] == "restricted" and espacios[nombre]["pod-security.kubernetes.io/audit"] == "restricted"
        assert "pod-security.kubernetes.io/enforce" not in espacios[nombre], f"{nombre} solo avisa; rechazar exige otra decisión"


def test_la_entrada_al_hub_llega_solo_a_los_puertos_que_cada_origen_usa():
    politica = next(d for d in _docs(HUB / "networkpolicy.yaml") if d["metadata"]["name"] == "permitir-traefik-alertmanager-y-propio")
    propio, traefik, monitoreo = politica["spec"]["ingress"]
    assert propio == {"from": [{"podSelector": {}}]}
    assert sorted(p["port"] for p in traefik["ports"]) == [7007, 8000, 8080]
    assert traefik["from"][0]["podSelector"] == {"matchLabels": {"app.kubernetes.io/name": "traefik"}}
    assert sorted(p["port"] for p in monitoreo["ports"]) == [8000, 8080]   # y nunca PostgreSQL (5432) ni voz (8100)
    puertos = {p["port"] for regla in politica["spec"]["ingress"] for p in regla.get("ports", [])}
    assert not puertos & {5432, 8100}


def test_los_pdb_no_bloquean_el_drenaje_del_nodo_unico():
    pdbs = [d for d in _docs(HUB / "escalado.yaml") if d["kind"] == "PodDisruptionBudget"]
    assert pdbs and all("minAvailable" not in p["spec"] and p["spec"]["maxUnavailable"] == 1 for p in pdbs)


def test_la_cuota_de_cada_cliente_limita_los_pods_en_kustomize_y_en_el_chart():
    base = _docs(REPO / "gitops/clients/_base/resourcequota.yaml")[0]["spec"]["hard"]
    assert base["pods"] == "10"
    assert 'pods: "10"' in (REPO / "gitops/charts/sitio-cliente/templates/cuota.yaml").read_text(encoding="utf-8")


def test_el_namespace_hub_tiene_limites_por_defecto():
    limites = _docs(HUB / "limitrange.yaml")[0]
    assert limites["kind"] == "LimitRange" and limites["metadata"]["namespace"] == "hub" and limites["spec"]["limits"][0]["default"]["memory"]


# ---------- OB-07, OB-09, OB-10 ----------


def test_de_traefik_solo_se_guardan_las_metricas_que_usan_los_tableros():
    trabajos = {j["job_name"]: j for j in yaml.safe_load((REPO / "observability/prometheus/prometheus.yml").read_text(encoding="utf-8"))["scrape_configs"]}
    regex = trabajos["traefik"]["metric_relabel_configs"][0]["regex"]
    assert re.fullmatch(regex, "traefik_service_requests_total") and re.fullmatch(regex, "traefik_service_request_duration_seconds_bucket")
    assert not re.fullmatch(regex, "traefik_entrypoint_open_connections")


def test_sitiocaido_sigue_activa_un_rato_despues_de_que_el_sitio_vuelve():
    regla = yaml.safe_load((REPO / "observability/prometheus/reglas/sitios.yml").read_text(encoding="utf-8"))["groups"][0]["rules"][0]
    assert regla["alert"] == "SitioCaido" and regla["keep_firing_for"] == "2m" and regla["for"] == "30s"


def test_el_panel_de_errores_no_confunde_un_tamano_con_un_error_5xx():
    import json

    tablero = json.loads((REPO / "observability/grafana/dashboards/servicio-sitios.json").read_text(encoding="utf-8"))
    consultas = [t["expr"] for p in tablero["panels"] for t in p.get("targets", []) if "|~" in t.get("expr", "")]
    errores = next(c for c in consultas if "error" in c)
    patron = re.search(r'\|~ "(.*)"$', errores).group(1).replace("\\\\", "\\").replace('\\"', '"')
    regex = re.compile(patron.replace("(?i)", ""), re.IGNORECASE)
    assert regex.search('GET /health HTTP/1.1" 503 12') and regex.search("ERROR al conectar")
    assert not regex.search("respuesta de 5120 bytes en 503 ms") and not regex.search("puerto 5432 abierto")


# ---------- IA-02, IA-03, IA-05, IA-07, IA-08 ----------


@pytest.mark.parametrize("ruta", ["gitops/platform/backstage/publicar-docs.sh", "infra/estado-remoto.sh", "gitops/pruebas/helm-vs-kustomize.sh"])
def test_las_herramientas_de_apoyo_van_fijadas_por_digest(ruta):
    lineas = [ln for ln in (REPO / ruta).read_text(encoding="utf-8").splitlines() if re.search(r"(IMAGE|IMAGEN)=\"\$\{", ln)]
    assert lineas and all("@sha256:" in ln and ":latest" not in ln for ln in lineas), lineas


def test_el_piso_de_opentofu_cubre_use_lockfile():
    texto = (REPO / "infra/tofu/providers.tf").read_text(encoding="utf-8")
    assert re.search(r'required_version\s*=\s*">= 1\.1[0-9]\.\d+"', texto)


SCRIPTS_CON_GITEA = [
    "gitops/hub/crear-tokens.sh", "gitops/platform/gitea/sembrar-hub-gitops.sh", "gitops/staging/promover.sh", "gitops/staging/publicar.sh",
    "pipelines/configurar-gitea.sh", "pipelines/sembrar-repos-sitios.sh", "demo/reiniciar-cluster.sh",
]


@pytest.mark.parametrize("ruta", SCRIPTS_CON_GITEA)
def test_la_contrasena_de_gitea_no_viaja_como_argumento_de_curl(ruta):
    texto = (REPO / ruta).read_text(encoding="utf-8")
    assert not re.search(r'curl[^\n]*\s-u\s+"', texto), f"{ruta} pasa la contraseña a curl con -u (visible en `ps`)"
    assert "lib-curl.sh" in texto and "cred_curl" in texto


def test_cred_curl_escapa_las_comillas_y_las_barras_de_la_clave(tmp_path):
    import subprocess

    biblioteca = (REPO / "gitops/lib-curl.sh").read_text(encoding="utf-8").replace("\r", "")   # en Windows el archivo de trabajo puede traer CRLF
    script = biblioteca + '\ncred_curl "usuario" \'cla"ve\\con\\barra\''
    salida = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout
    assert salida == 'user = "usuario:cla\\"ve\\\\con\\\\barra"\n'


@pytest.mark.parametrize("ruta", ["gitops/hub/respaldo/respaldar.sh", "gitops/hub/respaldo/restaurar.sh"])
def test_los_scripts_del_respaldo_usan_pipefail_cuando_el_shell_lo_tiene(ruta):
    assert "set -o pipefail" in (REPO / ruta).read_text(encoding="utf-8")


def test_la_cache_de_trivy_es_una_por_sitio():
    puerta = (REPO / "pipelines/puerta.sh").read_text(encoding="utf-8")
    assert 'CACHE_TRIVY="puerta-trivy-cache-${SITE}"' in puerta and "-v puerta-trivy-cache:" not in puerta
    assert puerta.count('-v "${CACHE_TRIVY}:/root/.cache"') == 4
