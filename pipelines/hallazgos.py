# Registro de hallazgos y VEX (spec 018, T02): cruza los reportes de Trivy (vulnerabilidades ALTAS y CRÍTICAS, también las que no tienen arreglo) con las decisiones de
# pipelines/hallazgos.yaml y deja tres cosas: la tabla del registro, el VEX en formato OpenVEX y el JSON completo. Frena (código 1) si queda un hallazgo
#   · corregible        ya tiene versión corregida: se corrige, no se acepta
#   · sin decisión      sin arreglo y sin regla en el registro
#   · con decisión vencida, o con una regla mal escrita (campos que faltan, justificación fuera del vocabulario de OpenVEX, revisión a más de 6 meses)
# Uso:  python pipelines/hallazgos.py --salida evidencias reporte1.json reporte2.json ...      (el nombre del archivo, sin .json, es el de la imagen)
import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
JUSTIFICATIONS = {
    "component_not_present",
    "vulnerable_code_not_present",
    "vulnerable_code_not_in_execute_path",
    "vulnerable_code_cannot_be_controlled_by_adversary",
    "inline_mitigations_already_exist",
}
MAX_DECISION_DAYS = 183
FIELDS = ("id", "estado", "explotabilidad", "tratamiento", "detalle", "revisar_en")


def validate_rules(registro: dict, hoy: date) -> list[str]:
    """Problemas de las reglas del registro; una decisión sin razón o sin fecha de revisión no cuenta como decisión."""
    problemas, vistos = [], set()
    for regla in registro.get("reglas", []):
        nombre = regla.get("id", "(sin id)")
        faltan = [c for c in FIELDS if not regla.get(c)]
        if faltan:
            problemas.append(f"regla {nombre}: faltan {', '.join(faltan)}")
        if nombre in vistos:
            problemas.append(f"regla {nombre}: id repetido")
        vistos.add(nombre)
        if not regla.get("paquetes") and not regla.get("cves"):
            problemas.append(f"regla {nombre}: sin paquetes ni cves, aplicaría a todo")
        if regla.get("estado") not in ("not_affected", "affected"):
            problemas.append(f"regla {nombre}: estado debe ser not_affected o affected")
        if regla.get("estado") == "not_affected" and regla.get("justificacion") not in JUSTIFICATIONS:
            problemas.append(f"regla {nombre}: not_affected necesita una justificación de OpenVEX ({', '.join(sorted(JUSTIFICATIONS))})")
        try:
            revisar = date.fromisoformat(str(regla.get("revisar_en")))
        except ValueError:
            problemas.append(f"regla {nombre}: revisar_en no es una fecha AAAA-MM-DD")
            continue
        if (revisar - hoy).days > MAX_DECISION_DAYS:
            problemas.append(f"regla {nombre}: revisar_en está a más de 6 meses ({revisar})")
    return problemas


def rule_for(hallazgo: dict, reglas: list[dict]) -> dict | None:
    """La regla que cubre el hallazgo: coincide el paquete (si la regla los lista) y el CVE (si la regla los lista)."""
    for regla in reglas:
        paquetes, cves = regla.get("paquetes") or [], regla.get("cves") or []
        if paquetes and hallazgo["paquete"] not in paquetes:
            continue
        if cves and hallazgo["cve"] not in cves:
            continue
        return regla
    return None


def findings_from(reportes: list[Path]) -> list[dict]:
    salida = []
    for ruta in reportes:
        reporte = json.loads(ruta.read_text(encoding="utf-8"))
        for resultado in reporte.get("Results", []):
            for v in resultado.get("Vulnerabilities") or []:
                if v["Severity"] not in ("HIGH", "CRITICAL"):
                    continue
                salida.append({"imagen": ruta.stem, "severidad": v["Severity"], "cve": v["VulnerabilityID"], "paquete": v["PkgName"],
                               "instalada": v.get("InstalledVersion", ""), "corregida": v.get("FixedVersion") or "", "titulo": (v.get("Title") or "")[:90]})
    return salida


def classify(hallazgos: list[dict], registro: dict, hoy: date) -> None:
    reglas = registro.get("reglas", [])
    for h in hallazgos:
        if h["corregida"]:
            h["tratamiento"], h["regla"] = "corregir", ""
            h["motivo"] = f"corregible: actualizar {h['paquete']} a {h['corregida']}"
            continue
        regla = rule_for(h, reglas)
        if regla is None:
            h["tratamiento"], h["regla"], h["motivo"] = "sin decisión", "", "sin arreglo y sin regla en pipelines/hallazgos.yaml"
        elif date.fromisoformat(str(regla["revisar_en"])) < hoy:
            h["tratamiento"], h["regla"], h["motivo"] = "vencida", regla["id"], f"la decisión «{regla['id']}» venció el {regla['revisar_en']}"
        else:
            h["tratamiento"], h["regla"], h["motivo"] = regla["tratamiento"], regla["id"], f"regla {regla['id']} hasta {regla['revisar_en']}"


def openvex(hallazgos: list[dict], registro: dict, ahora: datetime) -> dict:
    """Documento OpenVEX con una declaración por CVE y regla: los productos son las imágenes donde aparece."""
    reglas = {r["id"]: r for r in registro.get("reglas", [])}
    agrupado: dict[tuple[str, str], set[str]] = {}
    for h in hallazgos:
        if h["regla"] in reglas and h["tratamiento"] in ("aceptar", "mitigar"):
            agrupado.setdefault((h["cve"], h["regla"]), set()).add(h["imagen"])
    declaraciones = []
    for (cve, id_regla), imagenes in sorted(agrupado.items()):
        regla = reglas[id_regla]
        d = {"vulnerability": {"name": cve}, "products": [{"@id": f"pkg:oci/{imagen}"} for imagen in sorted(imagenes)], "status": regla["estado"]}
        if regla["estado"] == "not_affected":
            d["justification"] = regla["justificacion"]
            d["impact_statement"] = regla["detalle"].strip()
        else:
            d["action_statement"] = f"{regla['tratamiento'].capitalize()}: {regla['detalle'].strip()} Revisar el {regla['revisar_en']}."
        declaraciones.append(d)
    huella = hashlib.sha256(json.dumps(declaraciones, sort_keys=True).encode()).hexdigest()[:16]
    return {"@context": "https://openvex.dev/ns/v0.2.0", "@id": f"https://forjadigital.test/vex/{huella}", "author": "Forja Digital", "role": "Equipo de plataforma",
            "timestamp": ahora.isoformat(), "version": 1, "statements": declaraciones}


def table(hallazgos: list[dict], registro: dict) -> str:
    """Tabla en Markdown de los hallazgos agrupados por regla, con su tratamiento y fecha de revisión."""
    reglas = {r["id"]: r for r in registro.get("reglas", [])}
    filas = ["| Regla | Severidad | CVE | Paquetes | Imágenes | Explotabilidad | Tratamiento | Revisar en |", "|---|---|---:|---|---|---|---|---|"]
    grupos: dict[str, list[dict]] = {}
    for h in hallazgos:
        grupos.setdefault(h["regla"] or h["tratamiento"], []).append(h)
    for clave, lista in sorted(grupos.items()):
        regla = reglas.get(clave)
        filas.append(
            f"| {clave} | {'/'.join(sorted({h['severidad'] for h in lista}))} | {len({h['cve'] for h in lista})} | {', '.join(sorted({h['paquete'] for h in lista}))} "
            f"| {', '.join(sorted({h['imagen'] for h in lista}))} | {(regla or {}).get('explotabilidad', '—')[:80]} | {lista[0]['tratamiento']} | {(regla or {}).get('revisar_en', '—')} |"
        )
    return "\n".join(filas)


def main() -> int:
    """Clasifica los hallazgos de Trivy contra el registro de decisiones y escribe la tabla, el JSON y el VEX."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reportes", nargs="+", type=Path, help="reportes JSON de Trivy (con --severity HIGH,CRITICAL y sin --ignore-unfixed)")
    ap.add_argument("--registro", type=Path, default=ROOT / "pipelines" / "hallazgos.yaml")
    ap.add_argument("--salida", type=Path, default=ROOT / "evidencias")
    ap.add_argument("--hoy", default=None, help="fecha AAAA-MM-DD (para las pruebas); por defecto, hoy")
    args = ap.parse_args()
    hoy = date.fromisoformat(args.hoy) if args.hoy else date.today()
    registro = yaml.safe_load(args.registro.read_text(encoding="utf-8"))

    problemas = validate_rules(registro, hoy)
    hallazgos = findings_from(args.reportes)
    classify(hallazgos, registro, hoy)
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "hallazgos.json").write_text(json.dumps(hallazgos, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.salida / "hallazgos.md").write_text(table(hallazgos, registro) + "\n", encoding="utf-8")
    (args.salida / "vex.openvex.json").write_text(json.dumps(openvex(hallazgos, registro, datetime.now(timezone.utc)), ensure_ascii=False, indent=2), encoding="utf-8")

    print(table(hallazgos, registro))
    cuentas = {t: sum(1 for h in hallazgos if h["tratamiento"] == t) for t in sorted({h["tratamiento"] for h in hallazgos})}
    print(f"\n{len(hallazgos)} hallazgos altos o críticos: {cuentas or 'ninguno'}")
    frenan = [h for h in hallazgos if h["tratamiento"] in ("corregir", "sin decisión", "vencida")]
    for h in frenan[:12]:
        print(f"  ✕ {h['imagen']}: {h['severidad']} {h['cve']} en {h['paquete']} {h['instalada']}: {h['motivo']}")
    for p in problemas:
        print(f"  ✕ {p}")
    return 1 if frenan or problemas else 0


if __name__ == "__main__":
    sys.exit(main())
