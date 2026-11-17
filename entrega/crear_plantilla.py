# Genera entrega/plantilla.docx (estilos APA 7) a partir del reference.docx por defecto de pandoc.
# Uso (dentro de un contenedor con python-docx): python crear_plantilla.py base.docx plantilla.docx
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

FUENTE = "Times New Roman"


def fuente(estilo, tam=12, negrita=None, cursiva=None, nombre=FUENTE):
    f = estilo.font
    f.name = nombre
    f.size = Pt(tam)
    f.bold = negrita
    f.italic = cursiva
    f.color.rgb = None
    rpr = estilo.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), nombre)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]


def parrafo(estilo, alinea=WD_ALIGN_PARAGRAPH.LEFT, sangria=None, doble=True, antes=0, despues=0, izq=None, colgante=None):
    p = estilo.paragraph_format
    p.alignment = alinea
    # Sin sangría explícita (0) y no «ninguna»: así los estilos basados en «Body Text» no heredan la de 1,27 cm (celdas de tabla, encabezados)
    p.first_line_indent = sangria if sangria is not None else Inches(0)
    p.left_indent = izq
    if colgante is not None:
        p.left_indent = colgante
        p.first_line_indent = -colgante
    p.space_before = Pt(antes)
    p.space_after = Pt(despues)
    p.line_spacing_rule = WD_LINE_SPACING.DOUBLE if doble else WD_LINE_SPACING.SINGLE
    p.keep_together = False
    p.widow_control = True


def estilo(doc, nombre, tipo=WD_STYLE_TYPE.PARAGRAPH, base="Normal"):
    try:
        return doc.styles[nombre]
    except KeyError:
        s = doc.styles.add_style(nombre, tipo)
        if base:
            s.base_style = doc.styles[base]
        return s


def bordes_tabla(s):
    """APA: solo líneas horizontales (arriba, bajo el encabezado y abajo), sin verticales."""
    ppr = s.element.get_or_add_tblPr() if hasattr(s.element, "get_or_add_tblPr") else None
    if ppr is None:
        ppr = s.element.find(qn("w:tblPr"))
        if ppr is None:
            ppr = OxmlElement("w:tblPr")
            s.element.append(ppr)
    for viejo in ppr.findall(qn("w:tblBorders")):
        ppr.remove(viejo)
    b = OxmlElement("w:tblBorders")
    for lado, v in (("top", "single"), ("left", "nil"), ("bottom", "single"), ("right", "nil"), ("insideH", "nil"), ("insideV", "nil")):
        e = OxmlElement(f"w:{lado}")
        e.set(qn("w:val"), v)
        if v == "single":
            e.set(qn("w:sz"), "8")
            e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "000000")
        b.append(e)
    ppr.append(b)
    # Encabezado con línea inferior (estilo de condición «firstRow»)
    for viejo in s.element.findall(qn("w:tblStylePr")):
        s.element.remove(viejo)
    fila = OxmlElement("w:tblStylePr")
    fila.set(qn("w:type"), "firstRow")
    tcpr = OxmlElement("w:tcPr")
    tb = OxmlElement("w:tcBorders")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "8")
    bot.set(qn("w:space"), "0")
    bot.set(qn("w:color"), "000000")
    tb.append(bot)
    tcpr.append(tb)
    fila.append(tcpr)
    rpr = OxmlElement("w:rPr")
    n = OxmlElement("w:b")
    rpr.append(n)
    fila.append(rpr)
    s.element.append(fila)


def numero_de_pagina(seccion):
    h = seccion.header
    h.is_linked_to_previous = False
    p = h.paragraphs[0] if h.paragraphs else h.add_paragraph()
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tipo)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = texto
        run._element.append(e)
    run.font.name = FUENTE
    run.font.size = Pt(12)


def main(entrada, salida):
    doc = Document(entrada)
    s = doc.sections[0]
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    numero_de_pagina(s)

    st = doc.styles
    # Texto corrido: Times 12, doble espacio, izquierda, sangría de 1,27 cm
    for nombre in ("Normal", "Body Text", "First Paragraph"):
        e = estilo(doc, nombre)
        fuente(e)
        parrafo(e, sangria=Inches(0.5))
    parrafo(st["Normal"], sangria=None)
    # Compacto (celdas de tabla y listas): un espacio, sin sangría
    c = estilo(doc, "Compact")
    fuente(c, 10)
    parrafo(c, doble=False)
    # Encabezados APA 1 a 5
    h = {
        "Heading 1": dict(negrita=True, cursiva=False, alinea=WD_ALIGN_PARAGRAPH.CENTER, sangria=None),
        "Heading 2": dict(negrita=True, cursiva=False, alinea=WD_ALIGN_PARAGRAPH.LEFT, sangria=None),
        "Heading 3": dict(negrita=True, cursiva=True, alinea=WD_ALIGN_PARAGRAPH.LEFT, sangria=None),
        "Heading 4": dict(negrita=True, cursiva=False, alinea=WD_ALIGN_PARAGRAPH.LEFT, sangria=Inches(0.5)),
        "Heading 5": dict(negrita=True, cursiva=True, alinea=WD_ALIGN_PARAGRAPH.LEFT, sangria=Inches(0.5)),
    }
    for nombre, d in h.items():
        e = estilo(doc, nombre)
        fuente(e, 12, d["negrita"], d["cursiva"])
        parrafo(e, d["alinea"], d["sangria"])
        e.paragraph_format.keep_with_next = True
    # Título del documento (portada): negrita, centrado
    t = estilo(doc, "Title")
    fuente(t, 12, True, False)
    parrafo(t, WD_ALIGN_PARAGRAPH.CENTER, None, antes=0)
    for nombre in ("Subtitle", "Author", "Date", "Abstract"):
        e = estilo(doc, nombre)
        fuente(e, 12, False, False)
        parrafo(e, WD_ALIGN_PARAGRAPH.CENTER if nombre != "Abstract" else WD_ALIGN_PARAGRAPH.LEFT, None)
        # El estilo por defecto de pandoc los deja «con el siguiente»: un resumen largo arrastraba el encabezado a una página aparte
        e.paragraph_format.keep_with_next = False
    # Rótulos de tabla y figura: pandoc usa «Table Caption» e «Image Caption».
    # APA: «Tabla N» en negrita arriba; el título en cursiva va en el texto de la leyenda.
    for nombre in ("Table Caption", "Image Caption", "Caption"):
        e = estilo(doc, nombre)
        fuente(e, 12, False, True)
        parrafo(e, WD_ALIGN_PARAGRAPH.LEFT, None, doble=False, despues=6)
        # La leyenda va arriba (tabla y figura): no puede quedar sola al pie de la página
        e.paragraph_format.keep_with_next = nombre in ("Table Caption", "Image Caption")
    # Nota de tabla o figura («Nota.»)
    n = estilo(doc, "Nota")
    fuente(n, 10)
    parrafo(n, doble=False, despues=12)
    # Citas largas (40 palabras o más): bloque con sangría de 1,27 cm
    b = estilo(doc, "Block Text")
    fuente(b)
    parrafo(b, sangria=None, izq=Inches(0.5))
    # Código: monoespaciada, un espacio
    for nombre in ("Source Code", "Verbatim Char"):
        try:
            e = st[nombre]
        except KeyError:
            continue
        fuente(e, 10 if nombre == "Verbatim Char" else 9, nombre="Consolas")
        if nombre == "Source Code":
            parrafo(e, doble=False, antes=0, despues=6)
    # Referencias con sangría francesa
    r = estilo(doc, "Referencia")
    fuente(r)
    parrafo(r, colgante=Inches(0.5))
    # Tablas
    try:
        bordes_tabla(st["Table"])
    except KeyError:
        pass
    # Tabla de contenido y enlaces
    for nombre in ("TOC Heading", "Hyperlink"):
        try:
            e = st[nombre]
        except KeyError:
            continue
        fuente(e, 12, nombre == "TOC Heading", False)
        if nombre == "Hyperlink":
            e.font.color.rgb = None
            e.font.underline = False
    # Word actualiza los campos (índice) al abrir el documento: pandoc solo deja el campo con un texto de aviso
    ajustes = doc.settings.element
    if ajustes.find(qn("w:updateFields")) is None:
        campo = OxmlElement("w:updateFields")
        campo.set(qn("w:val"), "true")
        ajustes.append(campo)
    doc.save(salida)
    print("plantilla:", salida)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
