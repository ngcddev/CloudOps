# PDF de los reportes mensuales (spec 013, CA-4) a partir de los datos congelados en `reports.data`. Blanco y negro, A4, sin servicios externos:
# reportlab es Python puro (no necesita las librerías del sistema que arrastra WeasyPrint). El ejecutivo se encoge para caber SIEMPRE en una
# página (CA-2) aunque haya varias fallas con mensajes largos; el operativo, que es interno, puede ocupar más de una.
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepInFrame, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.sla import BOGOTA

NEGRO = colors.black
GRIS = colors.HexColor("#555555")
LINEA = colors.HexColor("#999999")

_base = getSampleStyleSheet()
TITULO = ParagraphStyle("titulo", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_LEFT, spaceAfter=2)
SUBTITULO = ParagraphStyle("subtitulo", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=13, textColor=GRIS, spaceAfter=8)
SECCION = ParagraphStyle("seccion", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=10, spaceAfter=3)
TEXTO = ParagraphStyle("texto", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=13.5)
PIE = ParagraphStyle("pie", parent=_base["Normal"], fontName="Helvetica", fontSize=8, leading=10, textColor=GRIS)
CELDA = ParagraphStyle("celda", parent=TEXTO, fontSize=8, leading=10)
CELDA_NEGRITA = ParagraphStyle("celda_negrita", parent=CELDA, fontName="Helvetica-Bold")


def _numero(valor: float | None, decimales: int = 1, sufijo: str = "") -> str:
    """12345.6 → «12.345,6»; None → «sin datos» (nunca se inventa un cero)."""
    if valor is None:
        return "sin datos"
    texto = f"{valor:,.{decimales}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{texto}{sufijo}"


def _pesos(valor: float | None) -> str:
    return "sin datos" if valor is None else f"${valor:,.0f}".replace(",", ".")


def _fecha(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(BOGOTA).strftime("%d/%m/%Y %H:%M")


def _escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _tabla(filas: list[list], anchos: list[float], encabezado: bool = True) -> Table:
    tabla = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, LINEA), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if encabezado:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _pdf(elementos: list, pagina, margen: float, titulo: str) -> bytes:
    salida = io.BytesIO()
    SimpleDocTemplate(salida, pagesize=pagina, leftMargin=margen, rightMargin=margen, topMargin=margen, bottomMargin=margen, title=titulo, author="Forja Digital").build(elementos)
    return salida.getvalue()


def ejecutivo_pdf(datos: dict) -> bytes:
    """Una página A4 para el cliente: disponibilidad frente al objetivo, fallas, actualizaciones y solicitudes, en lenguaje simple."""
    margen = 20 * mm
    ancho, alto = A4[0] - 2 * margen, A4[1] - 2 * margen
    d, f = datos["disponibilidad"], datos["fallas"]
    contenido: list = [
        Paragraph(f"Reporte de su servicio · {_escapar(datos['etiqueta_mes'])}", TITULO),
        Paragraph(f"{_escapar(datos['cliente']['nombre'])} · {_escapar(datos['sitio'] or 'Sitio web')} · plan {_escapar(datos['plan'] or '')}".rstrip(" ·"), SUBTITULO),
        Paragraph("Disponibilidad de su sitio", SECCION),
    ]
    if d["valor"] is not None:
        contenido.append(Paragraph(f"<b>{_numero(d['valor'], 2, ' %')}</b> del tiempo disponible (objetivo acordado: {_numero(d['objetivo'], 1, ' %')}).", TEXTO))
    contenido.append(Paragraph(_escapar(d["texto"]), TEXTO))

    contenido.append(Paragraph("Fallas del mes", SECCION))
    if f["total"] == 0:
        contenido.append(Paragraph(_escapar(f["texto"]), TEXTO))
    else:
        if f["tiempo_de_recuperacion_promedio"]:
            contenido.append(Paragraph(f"Tiempo que tardamos en recuperar su sitio: {_escapar(f['tiempo_de_recuperacion_promedio'])} en promedio.", TEXTO))
        filas = [[Paragraph("Cuándo", CELDA_NEGRITA), Paragraph("Duración", CELDA_NEGRITA), Paragraph("Qué pasó", CELDA_NEGRITA)]]
        for falla in f["listadas"]:
            filas.append([Paragraph(_escapar(falla["cuando"]), CELDA), Paragraph(_escapar(falla["duracion"]), CELDA), Paragraph(_escapar(falla["texto"]), CELDA)])
        contenido.append(Spacer(1, 3))
        contenido.append(_tabla(filas, [28 * mm, 30 * mm, ancho - 58 * mm]))
        if f["sin_listar"]:
            contenido.append(Paragraph(f"Y {f['sin_listar']} falla(s) más de menor duración este mes.", PIE))

    contenido += [
        Paragraph("Actualizaciones de su sitio", SECCION), Paragraph(_escapar(datos["actualizaciones"]["texto"]), TEXTO),
        Paragraph("Sus solicitudes", SECCION), Paragraph(_escapar(datos["solicitudes"]["texto"]), TEXTO),
        Spacer(1, 14), Paragraph(f"Forja Digital · reporte generado el {_fecha(datos['generado'])} (hora de Colombia)", PIE),
    ]
    # El contenido se encoge si no cabe: el ejecutivo es siempre de una página (CA-2)
    return _pdf([KeepInFrame(ancho, alto, contenido, mode="shrink")], A4, margen, f"Reporte de su servicio · {datos['etiqueta_mes']}")


def operativo_pdf(datos: dict) -> bytes:
    """Reporte interno de la agencia (A4 horizontal): KPI por cliente, comparación con el mes anterior, totales y carga de los técnicos."""
    margen = 15 * mm
    ancho = landscape(A4)[0] - 2 * margen
    contenido: list = [
        Paragraph(f"Reporte operativo · {_escapar(datos['etiqueta_mes'])}", TITULO),
        Paragraph(f"Forja Digital · uso interno · comparado con {_escapar(datos['etiqueta_mes_anterior'])}", SUBTITULO),
        Paragraph("KPI por cliente", SECCION),
    ]
    encabezados = ["Cliente", "Plan", "Disponibilidad (SLO)", "SLA", "MTTR", "Fallas", "Solicitudes (ab./cerr.)", "Horas", "Costo"]
    filas = [[Paragraph(h, CELDA_NEGRITA) for h in encabezados]]
    for c in datos["clientes"]:
        disp = f"{_numero(c['disponibilidad'], 2, ' %')} ({_numero(c['slo'], 1, ' %')})" if c["disponibilidad"] is not None else f"sin datos ({_numero(c['slo'], 1, ' %')})"
        filas.append([
            Paragraph(_escapar(c["cliente"]), CELDA), Paragraph(_escapar(c["plan"] or "—"), CELDA), Paragraph(disp, CELDA),
            Paragraph(_numero(c["sla"], 1, " %"), CELDA), Paragraph(_numero(c["mttr"], 1, " min"), CELDA), Paragraph(str(c["incidentes"]), CELDA),
            Paragraph(f"{c['solicitudes_abiertas']} / {c['solicitudes_cerradas']}", CELDA), Paragraph(_numero(c["horas"], 1), CELDA), Paragraph(_pesos(c["costo"]), CELDA),
        ])
    t = datos["totales"]
    filas.append([
        Paragraph("Total", CELDA_NEGRITA), Paragraph("", CELDA), Paragraph("", CELDA), Paragraph(_numero(t["sla_promedio"], 1, " %") + " (prom.)", CELDA_NEGRITA),
        Paragraph(_numero(t["mttr_promedio"], 1, " min") + " (prom.)", CELDA_NEGRITA), Paragraph(str(t["incidentes"]), CELDA_NEGRITA),
        Paragraph(f"{t['solicitudes_abiertas']} / {t['solicitudes_cerradas']}", CELDA_NEGRITA), Paragraph(_numero(t["horas"], 1), CELDA_NEGRITA), Paragraph(_pesos(t["costo"]), CELDA_NEGRITA),
    ])
    contenido.append(_tabla(filas, [48 * mm, 22 * mm, 48 * mm, 28 * mm, 28 * mm, 16 * mm, 34 * mm, 18 * mm, ancho - 242 * mm]))
    contenido.append(Paragraph("SLA y MTTR promedio: promedio simple de los clientes que tienen dato; «sin datos» no cuenta como cero.", PIE))

    contenido.append(Paragraph(f"Comparación con {_escapar(datos['etiqueta_mes_anterior'])}", SECCION))
    comparacion = [[Paragraph(h, CELDA_NEGRITA) for h in ["Cliente", "SLA antes → ahora", "MTTR antes → ahora", "Horas antes → ahora", "Costo antes → ahora"]]]
    for c in datos["clientes"]:
        p = c["mes_anterior"]
        comparacion.append([
            Paragraph(_escapar(c["cliente"]), CELDA), Paragraph(f"{_numero(p['sla'], 1, ' %')} → {_numero(c['sla'], 1, ' %')}", CELDA),
            Paragraph(f"{_numero(p['mttr'], 1, ' min')} → {_numero(c['mttr'], 1, ' min')}", CELDA), Paragraph(f"{_numero(p['horas'], 1)} → {_numero(c['horas'], 1)}", CELDA),
            Paragraph(f"{_pesos(p['costo'])} → {_pesos(c['costo'])}", CELDA),
        ])
    contenido.append(_tabla(comparacion, [60 * mm, 55 * mm, 55 * mm, 45 * mm, ancho - 215 * mm]))

    contenido.append(Paragraph("Carga de los técnicos", SECCION))
    carga = [[Paragraph(h, CELDA_NEGRITA) for h in ["Técnico", "Horas registradas", "Carga del mes"]]]
    for tecnico in datos["tecnicos"]:
        carga.append([Paragraph(_escapar(tecnico["nombre"]), CELDA), Paragraph(_numero(tecnico["horas"], 1), CELDA), Paragraph(_numero(tecnico["carga"] * 100, 0, " %"), CELDA)])
    contenido.append(_tabla(carga, [70 * mm, 45 * mm, 45 * mm]))
    contenido += [Spacer(1, 10), Paragraph(f"Generado el {_fecha(datos['generado'])} (hora de Colombia). Las cifras son las de los tableros del Hub.", PIE)]
    return _pdf(contenido, landscape(A4), margen, f"Reporte operativo · {datos['etiqueta_mes']}")
