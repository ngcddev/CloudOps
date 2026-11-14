# Pruebas de la configuración de Backstage (spec 017, T02): la plantilla de sitio, la documentación como código y que todo esté registrado en el catálogo.
import re
from pathlib import Path

import yaml

BACKSTAGE = Path("/gitops/platform/backstage")


def _yaml(ruta: str) -> list[dict]:
    return [d for d in yaml.safe_load_all((BACKSTAGE / ruta).read_text(encoding="utf-8")) if d]


def _config() -> dict:
    return _yaml("app-config.hub.yaml")[0]


def _destinos() -> list[str]:
    return [loc["target"] for loc in _config()["catalog"]["locations"]]


def test_la_plantilla_es_un_template_valido_con_el_nombre_validado():
    plantilla = _yaml("templates/sitio-de-cliente.yaml")[0]

    assert plantilla["kind"] == "Template" and plantilla["apiVersion"] == "scaffolder.backstage.io/v1beta3"
    slug = plantilla["spec"]["parameters"][0]["properties"]["slug"]
    # El nombre acaba en una URL de Gitea: el patrón no deja pasar mayúsculas, espacios ni barras
    assert re.fullmatch(slug["pattern"], "colegio") and re.fullmatch(slug["pattern"], "san-marcos")
    assert not re.fullmatch(slug["pattern"], "Colegio Raro") and not re.fullmatch(slug["pattern"], "../x")
    assert [paso["action"] for paso in plantilla["spec"]["steps"]] == ["catalog:register"]


def test_la_plantilla_lee_el_catalog_info_que_escribe_el_hub():
    plantilla = _yaml("templates/sitio-de-cliente.yaml")[0]
    url = plantilla["spec"]["steps"][0]["input"]["catalogInfoUrl"]

    # Misma ruta que escribe provisioning.render_files: clients/<cliente>/catalog-info.yaml en hub-gitops
    assert url.endswith("/hub-gitops/src/branch/main/clients/${{ parameters.slug }}/catalog-info.yaml")


def test_el_catalogo_admite_plantillas_y_registra_la_plantilla_y_la_documentacion():
    config = _config()
    destinos = _destinos()

    assert "Template" in config["catalog"]["rules"][0]["allow"]
    assert any(d.endswith("platform/backstage/templates/sitio-de-cliente.yaml") for d in destinos)
    assert any(d.endswith("platform/backstage/docs/catalog-info.yaml") for d in destinos)


def test_la_documentacion_como_codigo_esta_completa():
    mkdocs = _yaml("docs/mkdocs.yml")[0]
    catalogo = _yaml("docs/catalog-info.yaml")[0]

    assert "techdocs-core" in mkdocs["plugins"]
    paginas = [archivo for entrada in mkdocs["nav"] for archivo in entrada.values()]
    assert paginas and all((BACKSTAGE / "docs" / "docs" / pagina).is_file() for pagina in paginas)
    assert catalogo["metadata"]["annotations"]["backstage.io/techdocs-ref"] == "dir:."


def test_techdocs_se_sirve_desde_un_volumen_que_sobrevive_a_los_reinicios():
    techdocs = _config()["techdocs"]
    despliegue = next(d for d in _yaml("deployment.yaml") if d["kind"] == "Deployment")
    pod = despliegue["spec"]["template"]["spec"]
    montajes = {m["name"]: m["mountPath"] for m in pod["containers"][0]["volumeMounts"]}

    # La imagen no trae mkdocs ni Docker: la documentación se genera fuera y Backstage solo la sirve
    assert techdocs["builder"] == "external"
    assert montajes["techdocs"] == techdocs["publisher"]["local"]["publishDirectory"]
    assert any(v["name"] == "techdocs" and "persistentVolumeClaim" in v for v in pod["volumes"])
    assert pod["securityContext"]["fsGroup"] == 1000
    assert any(d["kind"] == "PersistentVolumeClaim" and d["metadata"]["name"] == "backstage-techdocs" for d in _yaml("deployment.yaml"))


def test_el_catalogo_guarda_lo_registrado_en_un_volumen_y_no_en_memoria():
    """Con ':memory:' lo que registra la plantilla desaparecía en el siguiente reinicio (lo mostró la revisión de T02)."""
    conexion = _config()["backend"]["database"]["connection"]
    despliegue = next(d for d in _yaml("deployment.yaml") if d["kind"] == "Deployment")
    pod = despliegue["spec"]["template"]["spec"]
    montajes = {m["name"]: m["mountPath"] for m in pod["containers"][0]["volumeMounts"]}

    assert conexion != ":memory:" and conexion["directory"].startswith(montajes["datos"])
    assert any(v["name"] == "datos" and v["persistentVolumeClaim"]["claimName"] == "backstage-datos" for v in pod["volumes"])
    assert any(d["kind"] == "PersistentVolumeClaim" and d["metadata"]["name"] == "backstage-datos" for d in _yaml("deployment.yaml"))
    # SQLite en un volumen ReadWriteOnce: dos Pods a la vez se pisarían el archivo
    assert despliegue["spec"]["strategy"]["type"] == "Recreate"
