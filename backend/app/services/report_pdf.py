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

BLACK = colors.black
GRAY = colors.HexColor("#555555")
LINE = colors.HexColor("#999999")

_base = getSampleStyleSheet()
TITLE = ParagraphStyle("titulo", parent=_base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_LEFT, spaceAfter=2)
SUBTITLE = ParagraphStyle("subtitulo", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=13, textColor=GRAY, spaceAfter=8)
SECTION = ParagraphStyle("seccion", parent=_base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=10, spaceAfter=3)
BODY = ParagraphStyle("texto", parent=_base["Normal"], fontName="Helvetica", fontSize=10, leading=13.5)
FOOTER = ParagraphStyle("pie", parent=_base["Normal"], fontName="Helvetica", fontSize=8, leading=10, textColor=GRAY)
CELL = ParagraphStyle("celda", parent=BODY, fontSize=8, leading=10)
CELL_BOLD = ParagraphStyle("celda_negrita", parent=CELL, fontName="Helvetica-Bold")


def _number(valor: float | None, decimales: int = 1, sufijo: str = "") -> str:
    """12345.6 → «12.345,6»; None → «sin datos» (nunca se inventa un cero)."""
    if valor is None:
        return "sin datos"
    texto = f"{valor:,.{decimales}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{texto}{sufijo}"


def _cop(valor: float | None) -> str:
    return "sin datos" if valor is None else f"${valor:,.0f}".replace(",", ".")


def _date(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(BOGOTA).strftime("%d/%m/%Y %H:%M")


def _escape(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _table(filas: list[list], anchos: list[float], encabezado: bool = True) -> Table:
    tabla = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if encabezado:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _pdf(elementos: list, pagina, margen: float, titulo: str) -> bytes:
    salida = io.BytesIO()
    SimpleDocTemplate(salida, pagesize=pagina, leftMargin=margen, rightMargin=margen, topMargin=margen, bottomMargin=margen, title=titulo, author="Forja Digital").build(elementos)
    return salida.getvalue()


def executive_pdf(datos: dict) -> bytes:
    """Una página A4 para el cliente: disponibilidad frente al objetivo, fallas, actualizaciones y solicitudes, en lenguaje simple."""
    margen = 20 * mm
    ancho, alto = A4[0] - 2 * margen, A4[1] - 2 * margen
    d, f = datos["disponibilidad"], datos["fallas"]
    contenido: list = [
        Paragraph(f"Reporte de su servicio · {_escape(datos['etiqueta_mes'])}", TITLE),
        Paragraph(f"{_escape(datos['cliente']['nombre'])} · {_escape(datos['sitio'] or 'Sitio web')} · plan {_escape(datos['plan'] or '')}".rstrip(" ·"), SUBTITLE),
        Paragraph("Disponibilidad de su sitio", SECTION),
    ]
    if d["valor"] is not None:
        contenido.append(Paragraph(f"<b>{_number(d['valor'], 2, ' %')}</b> del tiempo disponible (objetivo acordado: {_number(d['objetivo'], 1, ' %')}).", BODY))
    contenido.append(Paragraph(_escape(d["texto"]), BODY))

    contenido.append(Paragraph("Fallas del mes", SECTION))
    if f["total"] == 0:
        contenido.append(Paragraph(_escape(f["texto"]), BODY))
    else:
        if f["tiempo_de_recuperacion_promedio"]:
            contenido.append(Paragraph(f"Tiempo que tardamos en recuperar su sitio: {_escape(f['tiempo_de_recuperacion_promedio'])} en promedio.", BODY))
        filas = [[Paragraph("Cuándo", CELL_BOLD), Paragraph("Duración", CELL_BOLD), Paragraph("Qué pasó", CELL_BOLD)]]
        for falla in f["listadas"]:
            filas.append([Paragraph(_escape(falla["cuando"]), CELL), Paragraph(_escape(falla["duracion"]), CELL), Paragraph(_escape(falla["texto"]), CELL)])
        contenido.append(Spacer(1, 3))
        contenido.append(_table(filas, [28 * mm, 30 * mm, ancho - 58 * mm]))
        if f["sin_listar"]:
            contenido.append(Paragraph(f"Y {f['sin_listar']} falla(s) más de menor duración este mes.", FOOTER))

    contenido += [
        Paragraph("Actualizaciones de su sitio", SECTION), Paragraph(_escape(datos["actualizaciones"]["texto"]), BODY),
        Paragraph("Sus solicitudes", SECTION), Paragraph(_escape(datos["solicitudes"]["texto"]), BODY),
        Spacer(1, 14), Paragraph(f"Forja Digital · reporte generado el {_date(datos['generado'])} (hora de Colombia)", FOOTER),
    ]
    # El contenido se encoge si no cabe: el ejecutivo es siempre de una página (CA-2)
    return _pdf([KeepInFrame(ancho, alto, contenido, mode="shrink")], A4, margen, f"Reporte de su servicio · {datos['etiqueta_mes']}")


def operational_pdf(datos: dict) -> bytes:
    """Reporte interno de la agencia (A4 horizontal): KPI por cliente, comparación con el mes anterior, totales y carga de los técnicos."""
    margen = 15 * mm
    ancho = landscape(A4)[0] - 2 * margen
    contenido: list = [
        Paragraph(f"Reporte operativo · {_escape(datos['etiqueta_mes'])}", TITLE),
        Paragraph(f"Forja Digital · uso interno · comparado con {_escape(datos['etiqueta_mes_anterior'])}", SUBTITLE),
        Paragraph("KPI por cliente", SECTION),
    ]
    encabezados = ["Cliente", "Plan", "Disponibilidad (SLO)", "SLA", "MTTR", "Fallas", "Solicitudes (ab./cerr.)", "Horas", "Costo"]
    filas = [[Paragraph(h, CELL_BOLD) for h in encabezados]]
    for c in datos["clientes"]:
        disp = f"{_number(c['disponibilidad'], 2, ' %')} ({_number(c['slo'], 1, ' %')})" if c["disponibilidad"] is not None else f"sin datos ({_number(c['slo'], 1, ' %')})"
        filas.append([
            Paragraph(_escape(c["cliente"]), CELL), Paragraph(_escape(c["plan"] or "—"), CELL), Paragraph(disp, CELL),
            Paragraph(_number(c["sla"], 1, " %"), CELL), Paragraph(_number(c["mttr"], 1, " min"), CELL), Paragraph(str(c["incidentes"]), CELL),
            Paragraph(f"{c['solicitudes_abiertas']} / {c['solicitudes_cerradas']}", CELL), Paragraph(_number(c["horas"], 1), CELL), Paragraph(_cop(c["costo"]), CELL),
        ])
    t = datos["totales"]
    filas.append([
        Paragraph("Total", CELL_BOLD), Paragraph("", CELL), Paragraph("", CELL), Paragraph(_number(t["sla_promedio"], 1, " %") + " (prom.)", CELL_BOLD),
        Paragraph(_number(t["mttr_promedio"], 1, " min") + " (prom.)", CELL_BOLD), Paragraph(str(t["incidentes"]), CELL_BOLD),
        Paragraph(f"{t['solicitudes_abiertas']} / {t['solicitudes_cerradas']}", CELL_BOLD), Paragraph(_number(t["horas"], 1), CELL_BOLD), Paragraph(_cop(t["costo"]), CELL_BOLD),
    ])
    contenido.append(_table(filas, [48 * mm, 22 * mm, 48 * mm, 28 * mm, 28 * mm, 16 * mm, 34 * mm, 18 * mm, ancho - 242 * mm]))
    contenido.append(Paragraph("SLA y MTTR promedio: promedio simple de los clientes que tienen dato; «sin datos» no cuenta como cero.", FOOTER))

    contenido.append(Paragraph(f"Comparación con {_escape(datos['etiqueta_mes_anterior'])}", SECTION))
    comparacion = [[Paragraph(h, CELL_BOLD) for h in ["Cliente", "SLA antes → ahora", "MTTR antes → ahora", "Horas antes → ahora", "Costo antes → ahora"]]]
    for c in datos["clientes"]:
        p = c["mes_anterior"]
        comparacion.append([
            Paragraph(_escape(c["cliente"]), CELL), Paragraph(f"{_number(p['sla'], 1, ' %')} → {_number(c['sla'], 1, ' %')}", CELL),
            Paragraph(f"{_number(p['mttr'], 1, ' min')} → {_number(c['mttr'], 1, ' min')}", CELL), Paragraph(f"{_number(p['horas'], 1)} → {_number(c['horas'], 1)}", CELL),
            Paragraph(f"{_cop(p['costo'])} → {_cop(c['costo'])}", CELL),
        ])
    contenido.append(_table(comparacion, [60 * mm, 55 * mm, 55 * mm, 45 * mm, ancho - 215 * mm]))

    contenido.append(Paragraph("Carga de los técnicos", SECTION))
    carga = [[Paragraph(h, CELL_BOLD) for h in ["Técnico", "Horas registradas", "Carga del mes"]]]
    for tecnico in datos["tecnicos"]:
        carga.append([Paragraph(_escape(tecnico["nombre"]), CELL), Paragraph(_number(tecnico["horas"], 1), CELL), Paragraph(_number(tecnico["carga"] * 100, 0, " %"), CELL)])
    contenido.append(_table(carga, [70 * mm, 45 * mm, 45 * mm]))
    contenido += [Spacer(1, 10), Paragraph(f"Generado el {_date(datos['generado'])} (hora de Colombia). Las cifras son las de los tableros del Hub.", FOOTER)]
    return _pdf(contenido, landscape(A4), margen, f"Reporte operativo · {datos['etiqueta_mes']}")
