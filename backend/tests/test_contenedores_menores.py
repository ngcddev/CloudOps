# Hallazgos menores de contenedores (spec 022, T36): CT-07 a CT-10, CT-12 y CT-13. Lo que protegen: CPU limitada en cada servicio, esperas con salud, /health en nginx,
# cabeceras de seguridad (sin scripts en línea, que la CSP no permite) y un contexto de build sin secretos.
import re
from pathlib import Path

import pytest
import yaml

REPO = Path("/repo")
COMPOSE = REPO / "docker-compose.yml"
FRONTEND = REPO / "frontend"

pytestmark = pytest.mark.skipif(not (COMPOSE.exists() and FRONTEND.exists()), reason="el repositorio no está montado en /repo")


def _compose(ruta: Path = COMPOSE) -> dict:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))["services"]


def test_todo_servicio_de_compose_tiene_limite_de_memoria_y_de_cpu():
    for ruta in (COMPOSE, REPO / "ai/servidor-mlflow/docker-compose.yml"):
        for nombre, servicio in _compose(ruta).items():
            assert servicio.get("mem_limit"), f"{nombre} no tiene mem_limit"
            assert servicio.get("cpus"), f"{nombre} no tiene cpus (auditoría CT-07)"


def test_web_y_consultorio_esperan_a_que_su_backend_este_sano():
    servicios = _compose()
    assert servicios["web"]["depends_on"]["api"] == {"condition": "service_healthy"}
    assert servicios["consultorio-web"]["depends_on"]["consultorio-api"] == {"condition": "service_healthy"}
    assert servicios["consultorio-api"]["healthcheck"]["test"]   # y ese backend tiene con qué responder (CT-08)


def test_las_imagenes_del_hub_traen_su_healthcheck():
    assert "HEALTHCHECK" in (REPO / "backend/Dockerfile").read_text(encoding="utf-8")
    assert (REPO / "backend/Dockerfile").read_text(encoding="utf-8").count("HEALTHCHECK") == 2   # dev y prod
    assert "/health" in (FRONTEND / "Dockerfile").read_text(encoding="utf-8") and "HEALTHCHECK" in (FRONTEND / "Dockerfile").read_text(encoding="utf-8")


def test_nginx_expone_health_y_las_sondas_del_hub_lo_usan():
    nginx = (FRONTEND / "nginx.conf").read_text(encoding="utf-8")
    assert re.search(r"location = /health \{[^}]*return 200", nginx, re.S)
    web = next(d for d in yaml.safe_load_all((REPO / "gitops/hub/web.yaml").read_text(encoding="utf-8")) if d and d.get("kind") == "Deployment")
    contenedor = web["spec"]["template"]["spec"]["containers"][0]
    assert contenedor["readinessProbe"]["httpGet"]["path"] == "/health" and contenedor["livenessProbe"]["httpGet"]["path"] == "/health"


def test_cada_location_que_agrega_cabeceras_incluye_las_de_seguridad():
    # En nginx un add_header dentro de un location anula los del nivel superior: sin el include, esa ruta saldría sin cabeceras (auditoría CT-13)
    nginx = (FRONTEND / "nginx.conf").read_text(encoding="utf-8")
    for bloque in re.findall(r"location [^{]*\{([^}]*)\}", nginx):
        if "add_header" in bloque:
            assert "include /etc/nginx/seguridad.conf;" in bloque, bloque
    assert "include /etc/nginx/seguridad.conf;" in re.split(r"\n\s*location\s", nginx, maxsplit=1)[0]   # y el nivel del servidor
    assert "COPY seguridad.conf /etc/nginx/seguridad.conf" in (FRONTEND / "Dockerfile").read_text(encoding="utf-8")


def test_las_cabeceras_de_seguridad_son_las_esperadas_y_la_csp_no_permite_scripts_en_linea():
    cabeceras = (FRONTEND / "seguridad.conf").read_text(encoding="utf-8")
    for nombre in ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"):
        assert f"add_header {nombre} " in cabeceras
    csp = re.search(r'add_header Content-Security-Policy "([^"]*)"', cabeceras).group(1)
    assert "script-src 'self'" in csp and "'unsafe-inline'" not in csp.split("style-src")[0] and "frame-ancestors 'none'" in csp
    assert "microphone=(self)" in cabeceras   # la entrada por voz del asistente sigue funcionando


def test_index_html_no_tiene_scripts_en_linea_porque_la_csp_los_bloquea():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    en_linea = [m for m in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html)]
    assert not en_linea, f"scripts en línea en index.html: {en_linea}"
    assert (FRONTEND / "public/tema-inicial.js").exists() and "tema-inicial.js" in html


@pytest.mark.parametrize("carpeta", ["backend", "frontend"])
def test_el_contexto_de_build_no_lleva_archivos_de_entorno(carpeta):
    lineas = (REPO / carpeta / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in lineas and ".env.*" in lineas and ".git" in lineas, f"{carpeta}/.dockerignore no excluye los .env"
