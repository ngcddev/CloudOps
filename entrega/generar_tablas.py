#!/usr/bin/env python3
# Genera las secciones 10 (historias), 22 (pruebas), 23 (trazabilidad) y 29 (anexos) del informe a partir de entrega/datos/*.csv.
# Esas cuatro secciones NO se editan a mano: se cambian los CSV y se vuelve a correr este script.
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"
INFORME = RAIZ / "00-informe"


def leer(nombre: str) -> list[dict]:
    with (DATOS / f"{nombre}.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def limpia(t: str) -> str:
    return t.replace("|", "\\|").replace("\n", " ").strip()


def tabla(encabezados: list[str], filas: list[list[str]], pesos: list[int]) -> str:
    sep = "|" + "|".join("-" * max(2, p) for p in pesos) + "|"
    out = ["| " + " | ".join(encabezados) + " |", sep]
    out += ["| " + " | ".join(limpia(c) for c in f) + " |" for f in filas]
    return "\n".join(out)


def leyenda(clave: str, titulo: str) -> str:
    # El número real lo asigna entrega/preprocesar.py según el orden del documento.
    return f'::: {{custom-style="Table Caption"}}\n**Tabla {{T:{clave}}}**\\\n*{titulo}*\n:::\n'


def nota(texto: str) -> str:
    return f'::: {{custom-style="Nota"}}\n*Nota.* {texto}\n:::\n'


def por_requisito(traza: list[dict]) -> dict[str, list[dict]]:
    return {t["requisito"]: t for t in traza}


def seccion_10(hu, traza, pruebas, evid) -> str:
    por_hu: dict[str, dict] = {h["hu"]: {"pf": [], "e": [], "rq": []} for h in hu}
    for t in traza:
        for h in t["historia"].split():
            if h in por_hu:
                por_hu[h]["rq"].append(t["requisito"])
                por_hu[h]["pf"] += [p for p in t["prueba"].split() if p.startswith("PF-")]
                por_hu[h]["e"] += [e for e in t["evidencia"].split() if e.startswith("E-")]
    filas = []
    for h in hu:
        d = por_hu[h["hu"]]
        orden = lambda xs: " ".join(sorted(set(xs)))  # noqa: E731
        filas.append([h["hu"], f"Como {h['rol'].lower()}, quiero {h['quiero']}, para {h['para']}.", orden(d["rq"]), h["componente"], orden(d["pf"]), orden(d["e"])])
    return (
        "<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/*.csv. No editar a mano. -->\n\n"
        "# Historias de usuario\n\n"
        "Las historias de usuario siguen el formato «Como [rol], quiero [acción], para [beneficio]» y se rastrean hasta los requerimientos que cubren, "
        "los componentes que las implementan, las pruebas funcionales que las verifican (sección Pruebas funcionales) y las evidencias que las respaldan (Apéndice A). "
        f"Se definieron {len(hu)} historias para tres roles humanos (administrador de la agencia, técnico de la agencia y cliente PyME) y para el operador de la plataforma, "
        "que corresponde al equipo de ingeniería. Los requerimientos RF-21 (diferido) y RF-24 (fuera de alcance) no tienen historia porque no se construyeron.\n\n"
        + leyenda("hu", "Historias de usuario y su trazabilidad")
        + "\n"
        + tabla(["ID", "Historia", "Requisitos", "Componentes", "Pruebas", "Evidencias"], filas, [6, 36, 12, 18, 10, 12])
        + "\n\n"
        + nota("Elaboración propia a partir de `entrega/datos/historias.csv` y `entrega/datos/trazabilidad.csv`. Las pruebas y evidencias de cada historia son las de los requisitos que cubre.")
    )


def seccion_22(pruebas) -> str:
    filas = [[p["pf"], p["caso"], p["requisitos"], p["entrada"], p["esperado"], p["obtenido"], p["estado"]] for p in pruebas]
    total = sum(int(p["obtenido"].split()[0]) for p in pruebas if p["obtenido"].split() and p["obtenido"].split()[0].isdigit())
    return (
        "<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/pruebas.csv. No editar a mano. -->\n\n"
        "# Pruebas funcionales\n\n"
        f"Las {len(pruebas)} pruebas funcionales (PF) agrupan los archivos de pruebas automatizadas que verifican cada requerimiento. "
        "Los resultados se obtuvieron el 16 de noviembre de 2026 ejecutando `python entrega/ejecutar_pruebas.py`, que corre `pytest` dentro del contenedor de la API para PF-01 a PF-25; "
        "PF-26 corresponde a las pruebas de `ai/` y se ejecutó con `cd ai && pytest` en un entorno aparte. "
        f"La suma de pruebas ejecutadas en la Tabla {{T:pf}} es {total}; las pruebas que pertenecen a varias PF no se cuentan dos veces en la suite completa (1.134 recogidas en el backend).\n\n"
        "**Condición de ejecución.** El entorno local define `ASSISTANT_CONTEXT_MODE=rag`, y seis pruebas del asistente suponen el modo por defecto (`completo`): con el entorno local fallan, con el valor por defecto pasan. "
        "La CI de GitHub no define esa variable, por lo que no se ve afectada. Para reproducir las condiciones de la CI, el script fija `ASSISTANT_CONTEXT_MODE=completo`. "
        "Es una debilidad de aislamiento de las pruebas (leen el entorno del proceso), no un defecto del producto, y queda anotada como mejora.\n\n"
        + leyenda("pf", "Pruebas funcionales: entrada, resultado esperado y resultado obtenido")
        + "\n"
        + tabla(["ID", "Caso", "Requisitos", "Entrada", "Resultado esperado", "Resultado obtenido", "Estado"], filas, [6, 16, 9, 20, 22, 14, 8])
        + "\n\n"
        + nota("Elaboración propia a partir de `entrega/datos/pruebas.csv`. El detalle de cada caso está en los archivos de `backend/tests/` y `ai/tests/` indicados en ese archivo. Las pruebas de plataforma que requieren el clúster (por ejemplo `gitops/pruebas/*.sh`) se citan como evidencia en el Apéndice A y no en esta tabla.")
    )


def seccion_23(traza) -> str:
    filas = [[t["requisito"], t["historia"], t["componente"], t["prueba"], t["evidencia"], t["estado"] + (f" ({t['nota']})" if t["nota"] else "")] for t in traza]
    return (
        "<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/trazabilidad.csv. No editar a mano. -->\n\n"
        "# Matriz de trazabilidad resumida\n\n"
        "La matriz relaciona cada requerimiento con su historia de usuario, el componente que lo implementa, la prueba que lo verifica, la evidencia y su estado. "
        "La versión completa y editable es el archivo complementario `02_Matriz_Trazabilidad.xlsx`; aquí se incluye la misma información sin columnas adicionales.\n\n"
        + leyenda("traza", "Matriz de trazabilidad: requisito, historia, componente, prueba, evidencia y estado")
        + "\n"
        + tabla(["Requisito", "Historia", "Componente", "Prueba", "Evidencia", "Estado"], filas, [9, 9, 18, 8, 12, 30])
        + "\n\n"
        + nota("Elaboración propia a partir de `entrega/datos/trazabilidad.csv`. «—» indica que el requisito no tiene historia, prueba o evidencia aplicable; el motivo está en el estado.")
    )


def seccion_26(lic) -> str:
    grupos: dict[str, list[dict]] = {}
    for fila in lic:
        grupos.setdefault(fila["grupo"], []).append(fila)
    cuerpo = []
    for n, (grupo, filas) in enumerate(grupos.items(), start=1):
        cuerpo.append(f"## {grupo}\n")
        cuerpo.append(leyenda(f"lic-{n}", f"Licencias: {grupo.lower()}"))
        cuerpo.append("\n" + tabla(["Componente", "Versión", "Licencia", "Uso en el proyecto", "Restricciones"], [[f["componente"], f["version"], f["licencia"], f["uso"], f["restriccion"]] for f in filas], [24, 10, 16, 22, 34]))
        cuerpo.append("\n\n" + nota("Elaboración propia a partir de `entrega/datos/licencias.csv`. Fuente de la licencia: " + ", ".join(sorted({f["fuente"] for f in filas})).lower() + ".") + "\n")
    restringidas = [f for f in lic if any(k in f["licencia"] for k in ("GPL", "AGPL", "BUSL", "Research", "Sin definir", "comerciales"))]
    return (
        "<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/licencias.csv. No editar a mano. -->\n\n"
        "# Licencias del software\n\n"
        f"Se registran {len(lic)} componentes, modelos y conjuntos de datos con su versión, licencia, uso y restricciones. "
        "Las licencias de las dependencias directas de Python y de JavaScript se leyeron de los metadatos de los paquetes instalados y del `package-lock.json` el 16 de noviembre de 2026; las de los modelos, de sus fichas (verificadas el 15 de noviembre de 2026 en Hugging Face y en la página de Ollama); "
        "las de la plataforma y de las herramientas son las que declara cada proyecto y **no se verificaron de nuevo en esta revisión**, por lo que deben confirmarse en el repositorio de cada proyecto antes de redistribuir. "
        "Las dependencias transitivas y los paquetes del sistema de las imágenes base no se listan: su inventario y sus licencias están en el SBOM (SPDX) que la puerta genera para cada imagen.\n\n"
        "## Lo que condiciona el uso\n\n"
        "Estas son las licencias que imponen condiciones o que quedan sin definir:\n\n"
        + "\n".join(f"- **{f['componente']}** ({f['licencia']}): {f['restriccion']}." for f in restringidas)
        + "\n\n**El código del proyecto no tiene licencia.** El repositorio no incluye un archivo `LICENSE`, y sin él el código se publica con todos los derechos reservados por defecto, aunque algunos documentos del repositorio lo describan como abierto. "
        "`[COMPLETAR: licencia del código del proyecto (por ejemplo MIT o Apache-2.0) y del material propio de evaluación; luego agregar el archivo LICENSE]`\n\n"
        + "\n".join(cuerpo)
    )


def seccion_29(evid) -> str:
    filas = [[e["e"], e["descripcion"], e["tipo"], e["requisitos"], e["estado"]] for e in evid]
    marcadores = []
    for e in evid:
        if e["estado"] == "pendiente":
            marcadores.append(f"[EVIDENCIA {e['e']} · {e['descripcion']} · {e['como_obtenerla']}]")
    return (
        "<!-- GENERADA por entrega/generar_tablas.py a partir de entrega/datos/evidencias.csv. No editar a mano. -->\n\n"
        "# Anexos\n\n"
        "## Apéndice A. Catálogo de evidencias\n\n"
        "Cada evidencia tiene un identificador E-nn que se cita en la matriz de trazabilidad. Las capturas y salidas marcadas como «pendiente» las incorpora el equipo en el lugar del marcador que sigue a la tabla; "
        "las marcadas como «existe» ya están en el repositorio.\n\n"
        + leyenda("ev", "Catálogo de evidencias")
        + "\n"
        + tabla(["ID", "Evidencia", "Tipo", "Requisitos", "Estado"], filas, [6, 40, 12, 14, 10])
        + "\n\n"
        + nota("Elaboración propia a partir de `entrega/datos/evidencias.csv`. La columna «cómo obtenerla» de cada evidencia está en ese archivo y en su marcador.")
        + "\n## Apéndice B. Evidencias por incorporar\n\n"
        + "\n\n".join(marcadores)
        + "\n\n## Apéndice C. Modalidad multimodal\n\n"
        "El componente multimodal adicional del proyecto es el audio: dictado y respuesta hablada del asistente (RF-27, evidencia E-18). "
        "La generación de imagen con ComfyUI, de video y de 3D no se construyó (ver la sección de alcance y las decisiones de arquitectura); por eso no hay capturas de esas herramientas.\n"
    )


TITULAR = {
    "users": "Personas usuarias del Hub (agencia y clientes)",
    "clients": "Contactos de los negocios clientes",
    "audit_logs": "Personas usuarias del Hub",
    "work_logs": "Técnicos de la agencia",
}


def inyectar(archivo: Path, marca: str, contenido: str) -> None:
    """Reemplaza lo que hay entre `<!-- MARCA:inicio -->` y `<!-- MARCA:fin -->` en una sección escrita a mano."""
    texto = archivo.read_text(encoding="utf-8")
    inicio, fin = f"<!-- {marca}:inicio -->", f"<!-- {marca}:fin -->"
    a, b = texto.index(inicio) + len(inicio), texto.index(fin)
    archivo.write_text(texto[:a] + "\n" + contenido + "\n" + texto[b:], encoding="utf-8")


def bloque_personales(dic) -> str:
    filas = []
    for d in dic:
        if d["personal"] == "No":
            continue
        titular = TITULAR.get(d["tabla"], "Quien escriba el texto")
        filas.append([f"`{d['tabla']}.{d['columna']}`", d["personal"], titular, d["descripcion"]])
    return (
        leyenda("personales", "Columnas con datos personales o que pueden contenerlos")
        + "\n"
        + tabla(["Columna", "Clasificación", "Titular", "Descripción"], filas, [18, 14, 20, 40])
        + "\n\n"
        + nota("Elaboración propia a partir de `entrega/datos/diccionario.csv`. «Posible» indica texto libre o detalles que podrían incluir datos personales; en el laboratorio todos los datos son sintéticos.")
    )


def bloque_diccionario(dic) -> str:
    filas = [[f"`{d['tabla']}.{d['columna']}`", d["tipo"], d["nulo"], d["relacion"] or "—", d["descripcion"]] for d in dic]
    return (
        leyenda("diccionario", "Diccionario de datos: tablas y columnas")
        + "\n"
        + tabla(["Tabla y columna", "Tipo", "Nulo", "Relación", "Descripción"], filas, [22, 12, 5, 14, 44])
        + "\n\n"
        + nota("Elaboración propia, generada con `entrega/generar_diccionario.py` a partir de los modelos de `backend/app/models/`.")
    )


def main() -> None:
    hu, pruebas, evid, traza = leer("historias"), leer("pruebas"), leer("evidencias"), leer("trazabilidad")
    (INFORME / "10-historias-de-usuario.md").write_text(seccion_10(hu, traza, pruebas, evid), encoding="utf-8")
    (INFORME / "22-pruebas-funcionales.md").write_text(seccion_22(pruebas), encoding="utf-8")
    (INFORME / "23-matriz-de-trazabilidad.md").write_text(seccion_23(traza), encoding="utf-8")
    (INFORME / "29-anexos.md").write_text(seccion_29(evid), encoding="utf-8")
    dic = leer("diccionario")
    s13 = INFORME / "13-modelo-de-datos.md"
    inyectar(s13, "PERSONALES", bloque_personales(dic))
    inyectar(s13, "DICCIONARIO", bloque_diccionario(dic))
    (INFORME / "26-licencias-del-software.md").write_text(seccion_26(leer("licencias")), encoding="utf-8")
    print("secciones 10, 13 (tablas), 22, 23, 26 y 29 generadas")


if __name__ == "__main__":
    main()
