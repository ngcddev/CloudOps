#!/usr/bin/env python3
# Verifica el informe consolidador (spec 023, T02): las 29 secciones, su encabezado y los marcadores pendientes.
# Uso: python entrega/verificar.py            errores si falta o sobra una sección; informa los pendientes
#      python entrega/verificar.py --estricto  además falla si queda cualquier marcador [COMPLETAR] o sin catalogar
import csv
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECCIONES = Path(__file__).resolve().parent / "00-informe"
ESPERADAS = 29
DATOS = Path(__file__).resolve().parent / "datos"
ESTADOS = {"Cumplido", "Parcial", "No verificado", "Diferido", "Fuera de alcance"}


def leer(nombre: str) -> list[dict]:
    with (DATOS / f"{nombre}.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def verificar_trazabilidad(errores: list[str]) -> None:
    """Columna vertebral: requisitos de las secciones 8 y 9, historias, pruebas, evidencias y su coherencia mutua."""
    historias, pruebas, evid, traza = leer("historias"), leer("pruebas"), leer("evidencias"), leer("trazabilidad")
    h_por = {h["hu"]: h for h in historias}
    p_por = {p["pf"]: p for p in pruebas}
    e_por = {e["e"]: e for e in evid}
    t_por = {r["requisito"]: r for r in traza}
    if len(t_por) != len(traza):
        errores.append("trazabilidad.csv: requisitos repetidos")
    # Requisitos del texto (secciones 8 y 9) frente a la matriz
    en_texto: set[str] = set()
    for nombre in ("08-requerimientos-funcionales.md", "09-requerimientos-no-funcionales.md"):
        en_texto |= set(re.findall(r"^\| ((?:RF|RNF)-\d{2}) \|", (SECCIONES / nombre).read_text(encoding="utf-8"), flags=re.M))
    if en_texto != set(t_por):
        errores.append(f"requisitos de las secciones 8 y 9 distintos de la matriz: solo en texto {sorted(en_texto - set(t_por))}, solo en matriz {sorted(set(t_por) - en_texto)}")
    for r in traza:
        rq = r["requisito"]
        if r["estado"] not in ESTADOS:
            errores.append(f"{rq}: estado «{r['estado']}» no permitido")
        for campo in ("historia", "componente", "prueba", "evidencia"):
            if r[campo].strip() == "—" and not r["nota"].strip():
                errores.append(f"{rq}: «{campo}» vacío sin nota que lo explique")
        for h in (x for x in r["historia"].split() if x != "—"):
            if h not in h_por:
                errores.append(f"{rq}: la historia {h} no existe")
            elif rq not in h_por[h]["rf"].split():
                errores.append(f"{rq}: la historia {h} no lo lista entre sus requisitos")
        for pf in (x for x in r["prueba"].split() if x != "—"):
            if pf not in p_por:
                errores.append(f"{rq}: la prueba {pf} no existe")
            elif rq not in p_por[pf]["requisitos"].split():
                errores.append(f"{rq}: la prueba {pf} no lo lista entre sus requisitos")
        for e in (x for x in r["evidencia"].split() if x != "—"):
            if e not in e_por:
                errores.append(f"{rq}: la evidencia {e} no existe")
            elif rq not in e_por[e]["requisitos"].split():
                errores.append(f"{rq}: la evidencia {e} no lo lista entre sus requisitos")
    for h in historias:
        for rq in h["rf"].split():
            if rq not in t_por:
                errores.append(f"{h['hu']}: el requisito {rq} no está en la matriz")
            elif h["hu"] not in t_por[rq]["historia"].split():
                errores.append(f"{h['hu']}: la matriz no lo asigna a {rq}")
    usadas_pf = {x for r in traza for x in r["prueba"].split()}
    usadas_e = {x for r in traza for x in r["evidencia"].split()}
    for pf, p in p_por.items():
        if pf not in usadas_pf:
            errores.append(f"{pf}: ningún requisito la usa")
        if p["estado"] != "Cumplido":
            errores.append(f"{pf}: estado «{p['estado']}» ({p['obtenido']})")
        for rq in p["requisitos"].split():
            if rq not in t_por:
                errores.append(f"{pf}: el requisito {rq} no está en la matriz")
    for e in e_por:
        if e not in usadas_e:
            errores.append(f"{e}: ninguna fila de la matriz la cita")
    print(f"Matriz: {len(traza)} requisitos · {len(historias)} historias · {len(pruebas)} pruebas · {len(evid)} evidencias")


RUTA = re.compile(r"^((?:[\w.-]+/)+[\w.-]+)(?::(\d+)(?:-(\d+))?)?(?:,\d+(?:-\d+)?)*$")
PREFIJOS = ("", "backend/app/", "backend/", "backend/tests/")
RAICES = ("backend", "frontend", "gitops", "observability", "pipelines", "infra", "ai", "voz", "docs", "runbooks", "specs", "constitution", "demo", "entrega", ".github")


def verificar_rutas(errores: list[str]) -> None:
    """Toda ruta citada entre comillas invertidas existe, y toda línea citada cabe en el archivo."""
    vistas = 0
    for a in sorted(SECCIONES.glob("[0-9][0-9]-*.md")):
        texto = re.sub(r"<!--.*?-->", "", a.read_text(encoding="utf-8"), flags=re.S)
        for tok in set(re.findall(r"`([^`\n]+)`", texto)):
            m = RUTA.match(tok)
            if not m or not (m.group(1).endswith("/") or re.search(r"\.\w+$", m.group(1))):
                continue
            ruta = m.group(1)
            if "{" in ruta or "*" in ruta:
                continue
            destino = next((RAIZ / p / ruta for p in PREFIJOS if (RAIZ / p / ruta).exists()), None)
            if ruta.split("/")[0] not in RAICES and destino is None and not any(ruta.startswith(r) for r in ("routers/", "services/", "integrations/")):
                continue
            vistas += 1
            if destino is None:
                errores.append(f"{a.name}: la ruta «{tok}» no existe")
            elif m.group(2) and destino.is_file():
                largo = len(destino.read_text(encoding="utf-8", errors="replace").splitlines())
                if int(m.group(3) or m.group(2)) > largo:
                    errores.append(f"{a.name}: «{tok}» pasa del final del archivo ({largo} líneas)")
    print(f"Rutas citadas comprobadas: {vistas}")


ALIAS_AUTOR = {
    "departamento nacional de planeación": "dnp",
    "congreso de la república de colombia": "congreso",
    "national institute of standards and technology": "nist",
    "ministerio de tecnologías de la información y las comunicaciones": "mintic",
}
TERMINOS = [
    "Cloud native", "Kubernetes", "GitOps", "IaC", "DevSecOps", "SBOM", "SLSA", "SLI", "SLO", "RAG", "LLM", "SLM", "MLOps", "LLMOps",
    "Inyección de instrucciones", "Embedding", "Índice vectorial", "Rollback", "Runbook",
]
NORMAS = ["Ley 1581", "CONPES 4144", "MinTIC", "NIST SP 800-218", "SLSA v1.2", "ISO/IEC 27001", "ISO/IEC 42001", "ISO/IEC 25010"]
CITA = re.compile(r"\(([^()]*?(?:\d{4}[a-z]?|s\. f\.))\)")


def clave_cita(texto: str) -> str:
    """De «Autor [SIGLA]» saca la clave del autor: la sigla si existe, el alias si es un nombre conocido o el primer apellido."""
    sigla = re.search(r"\[([^\]]+)\]", texto)
    nombre = re.sub(r"\s*\[[^\]]+\]", "", texto).strip()
    if sigla:
        return sigla.group(1).lower()
    nombre = re.sub(r"\s+et al\.?$", "", nombre).strip().lower()
    return ALIAS_AUTOR.get(nombre, nombre)


def verificar_referencias(errores: list[str]) -> None:
    """Toda cita (Autor, año) del texto tiene su referencia y toda referencia se cita (APA 7)."""
    refs_texto = (SECCIONES / "28-referencias.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"<!-- ref: ([^>]+?) -->", refs_texto))
    citadas: set[str] = set()
    for a in sorted(SECCIONES.glob("[0-9][0-9]-*.md")):
        if a.name.startswith("28-"):
            continue
        texto = re.sub(r"<!--.*?-->", "", a.read_text(encoding="utf-8"), flags=re.S)
        texto = re.sub(r"`[^`\n]*`", "", texto)
        for m in CITA.finditer(texto):
            for grupo in m.group(1).split(";"):
                partes = [p.strip() for p in grupo.split(",")]
                anios = []
                while partes and re.fullmatch(r"\d{4}[a-z]?|s\. f\.", partes[-1]):
                    anios.insert(0, partes.pop())
                if not anios or not partes:
                    continue
                autor = clave_cita(", ".join(partes))
                for anio in anios:
                    clave = f"{autor}|{anio}"
                    citadas.add(clave)
                    if clave not in refs:
                        errores.append(f"{a.name}: la cita ({', '.join(partes)}, {anio}) no tiene referencia «{clave}»")
    for r in sorted(refs - citadas):
        errores.append(f"28-referencias.md: la referencia «{r}» no se cita en el texto")
    print(f"Referencias: {len(refs)} · citas distintas en el texto: {len(citadas)}")


def verificar_glosario_y_normas(errores: list[str]) -> None:
    glosario = (SECCIONES / "27-glosario.md").read_text(encoding="utf-8").lower()
    for t in TERMINOS:
        if f"| {t.lower()}" not in glosario:
            errores.append(f"27-glosario.md: falta el término «{t}»")
    normas = (SECCIONES / "06-marco-normativo.md").read_text(encoding="utf-8")
    for n in NORMAS:
        if n not in normas:
            errores.append(f"06-marco-normativo.md: falta la norma «{n}»")


MARCADOR = re.compile(r"\[(COMPLETAR|FIGURA|EVIDENCIA)\b[^\]]*\]")


def main() -> int:
    estricto = "--estricto" in sys.argv
    errores: list[str] = []
    archivos = sorted(SECCIONES.glob("[0-9][0-9]-*.md"))
    numeros = [int(a.name[:2]) for a in archivos]
    faltan = sorted(set(range(1, ESPERADAS + 1)) - set(numeros))
    if faltan:
        errores.append(f"faltan las secciones {faltan}")
    repetidas = sorted({n for n in numeros if numeros.count(n) > 1})
    if repetidas:
        errores.append(f"secciones repetidas: {repetidas}")
    if len(archivos) > ESPERADAS:
        errores.append(f"hay {len(archivos)} archivos y se esperan {ESPERADAS}")

    cuenta = {"COMPLETAR": 0, "FIGURA": 0, "EVIDENCIA": 0}
    ids_figura: list[str] = []
    ids_evidencia: list[str] = []
    for a in archivos:
        texto = a.read_text(encoding="utf-8")
        h1 = [linea for linea in texto.splitlines() if linea.startswith("# ")]
        # La portada (02) se arma con estilos, no con un encabezado.
        if a.name[:2] != "02" and len(h1) != 1:
            errores.append(f"{a.name}: debe tener exactamente un encabezado de nivel 1 (tiene {len(h1)})")
        sin_comentarios = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
        for m in MARCADOR.finditer(sin_comentarios):
            cuenta[m.group(1)] += 1
            if m.group(1) == "FIGURA":
                ids_figura.append(m.group(0))
            if m.group(1) == "EVIDENCIA":
                ids_evidencia.append(m.group(0))

    for tipo, lista, patron in (("FIGURA", ids_figura, r"\[FIGURA F-\d{2} · "), ("EVIDENCIA", ids_evidencia, r"\[EVIDENCIA E-\d{2} · ")):
        for m in lista:
            if not re.match(patron, m):
                errores.append(f"marcador mal formado: {m[:70]}")
        ids = [re.search(r"[FE]-\d{2}", m).group(0) for m in lista if re.search(r"[FE]-\d{2}", m)]
        if len(ids) != len(set(ids)):
            errores.append(f"identificadores de {tipo} repetidos")

    verificar_trazabilidad(errores)
    verificar_rutas(errores)
    verificar_referencias(errores)
    verificar_glosario_y_normas(errores)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import preprocesar

    errores += preprocesar.combinar()[1]
    print(f"Secciones: {len(archivos)}/{ESPERADAS}")
    print(f"Pendientes: {cuenta['COMPLETAR']} por completar · {cuenta['FIGURA']} figuras · {cuenta['EVIDENCIA']} evidencias")
    if estricto and cuenta["COMPLETAR"]:
        errores.append(f"quedan {cuenta['COMPLETAR']} marcadores [COMPLETAR]")
    for e in errores:
        print("✗", e)
    if not errores:
        print("✓ estructura correcta")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
