# Pruebas del registro de hallazgos y el VEX (spec 018, T02): lo corregible se corrige, lo aceptado tiene regla vigente, una regla mal escrita o vencida frena, y el VEX sale en OpenVEX.
import importlib.util
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

RUTA = Path("/pipelines/hallazgos.py")
spec = importlib.util.spec_from_file_location("hallazgos", RUTA)
hallazgos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hallazgos)

REGISTRO = yaml.safe_load(Path("/pipelines/hallazgos.yaml").read_text(encoding="utf-8")) if Path("/pipelines/hallazgos.yaml").exists() else None
HOY = date(2026, 11, 15)


def _h(cve="CVE-2026-76642", paquete="mount", corregida="", imagen="hub-api"):
    return {"imagen": imagen, "severidad": "HIGH", "cve": cve, "paquete": paquete, "instalada": "1.0", "corregida": corregida, "titulo": "x"}


def _regla(**cambios):
    base = {"id": "r", "paquetes": ["mount"], "cves": ["CVE-2026-76642"], "estado": "not_affected", "justificacion": "vulnerable_code_not_in_execute_path",
            "explotabilidad": "local", "tratamiento": "aceptar", "detalle": "no se usa", "revisar_en": "2027-02-15"}
    base.update(cambios)
    return base


def test_el_registro_real_esta_bien_escrito_y_vigente():
    assert hallazgos.validate_rules(REGISTRO, HOY) == []
    assert len(REGISTRO["reglas"]) >= 5


def test_lo_que_tiene_arreglo_se_corrige_no_se_acepta():
    registro = {"reglas": [_regla()]}
    lista = [_h(corregida="1.2")]

    hallazgos.classify(lista, registro, HOY)

    assert lista[0]["tratamiento"] == "corregir"  # aunque una regla lo cubriría, con arreglo publicado no se acepta


def test_sin_arreglo_y_con_regla_se_acepta_y_sin_regla_frena():
    registro = {"reglas": [_regla()]}
    lista = [_h(), _h(cve="CVE-2026-1", paquete="otro")]

    hallazgos.classify(lista, registro, HOY)

    assert [h["tratamiento"] for h in lista] == ["aceptar", "sin decisión"]
    assert lista[0]["regla"] == "r"


def test_la_regla_exige_que_coincidan_el_paquete_y_el_cve():
    registro = {"reglas": [_regla()]}
    lista = [_h(paquete="mount", cve="CVE-OTRO"), _h(paquete="otro-paquete", cve="CVE-2026-76642")]

    hallazgos.classify(lista, registro, HOY)

    assert [h["tratamiento"] for h in lista] == ["sin decisión", "sin decisión"]


def test_una_decision_vencida_vuelve_a_frenar():
    registro = {"reglas": [_regla(revisar_en="2026-11-01")]}
    lista = [_h()]

    hallazgos.classify(lista, registro, HOY)

    assert lista[0]["tratamiento"] == "vencida"


@pytest.mark.parametrize("cambios, fragmento", [
    ({"detalle": ""}, "faltan detalle"),
    ({"justificacion": "porque_si"}, "justificación de OpenVEX"),
    ({"estado": "ignorado"}, "estado debe ser"),
    ({"revisar_en": "2028-01-01"}, "más de 6 meses"),
    ({"revisar_en": "pronto"}, "no es una fecha"),
    ({"paquetes": [], "cves": []}, "aplicaría a todo"),
])
def test_una_regla_mal_escrita_se_reporta(cambios, fragmento):
    problemas = hallazgos.validate_rules({"reglas": [_regla(**cambios)]}, HOY)

    assert any(fragmento in p for p in problemas), problemas


def test_el_vex_es_openvex_y_distingue_not_affected_de_affected():
    registro = {"reglas": [_regla(), _regla(id="s", paquetes=["libsqlite3-0"], cves=["CVE-2026-9"], estado="affected", tratamiento="mitigar", justificacion=None)]}
    lista = [_h(), _h(), _h(imagen="colegio-api"), _h(cve="CVE-2026-9", paquete="libsqlite3-0")]
    hallazgos.classify(lista, registro, HOY)

    vex = hallazgos.openvex(lista, registro, datetime(2026, 11, 15, tzinfo=timezone.utc))

    assert vex["@context"] == "https://openvex.dev/ns/v0.2.0" and vex["statements"]
    por_cve = {d["vulnerability"]["name"]: d for d in vex["statements"]}
    assert por_cve["CVE-2026-76642"]["status"] == "not_affected" and por_cve["CVE-2026-76642"]["justification"] == "vulnerable_code_not_in_execute_path"
    assert {p["@id"] for p in por_cve["CVE-2026-76642"]["products"]} == {"pkg:oci/hub-api", "pkg:oci/colegio-api"}
    assert por_cve["CVE-2026-9"]["status"] == "affected" and "Revisar el" in por_cve["CVE-2026-9"]["action_statement"]
    json.dumps(vex)  # serializable


def test_solo_las_altas_y_criticas_entran_al_registro(tmp_path):
    reporte = tmp_path / "imagen.json"
    reporte.write_text(json.dumps({"Results": [{"Vulnerabilities": [
        {"Severity": "MEDIUM", "VulnerabilityID": "CVE-1", "PkgName": "a"},
        {"Severity": "HIGH", "VulnerabilityID": "CVE-2", "PkgName": "b", "FixedVersion": "2"},
        {"Severity": "CRITICAL", "VulnerabilityID": "CVE-3", "PkgName": "c"},
    ]}]}), encoding="utf-8")

    lista = hallazgos.findings_from([reporte])

    assert [(h["cve"], h["imagen"]) for h in lista] == [("CVE-2", "imagen"), ("CVE-3", "imagen")]
