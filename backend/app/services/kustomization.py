# Edición de images.newTag en el kustomization.yaml de un cliente (spec 005, T10).
# Es una edición de texto línea a línea, no un volcado de YAML: así lo único que cambia en el
# commit de GitOps es la línea del tag (CA-2), con sus comentarios y su formato intactos.
import re

# Etiqueta de imagen válida de Docker; también evita meter saltos de línea o YAML en el archivo
_TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")
# `newTag: v1` con comentario opcional; conserva la sangría y el fin de línea de cada línea
_NEW_TAG = re.compile(r"^(?P<head>\s+(?:-\s+)?newTag:\s*)(?P<value>\"[^\"]*\"|'[^']*'|[^\s#]+)(?P<tail>.*)$")
# Valores que YAML leería como número o booleano si no van entre comillas
_AMBIGUOUS = re.compile(r"[0-9.]+|true|false|null|yes|no|on|off", re.IGNORECASE)


def _images_block(lines: list[str]) -> range:
    """Posiciones de las líneas que pertenecen a la clave `images:` de primer nivel."""
    start = next((i for i, line in enumerate(lines) if line.rstrip("\r\n") == "images:"), None)
    if start is None:
        raise ValueError("El kustomization.yaml no tiene la sección «images».")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        text = lines[i].rstrip("\r\n")
        # La sección termina en la siguiente clave de primer nivel (sin sangría y que no sea comentario)
        if text and not text[0].isspace() and not text.startswith(("#", "-")):
            end = i
            break
    return range(start + 1, end)


def get_tags(content: str) -> list[str]:
    """Devuelve los `newTag` de la sección `images`, en el orden del archivo."""
    lines = content.splitlines(keepends=True)
    tags = []
    for i in _images_block(lines):
        match = _NEW_TAG.match(lines[i].rstrip("\r\n"))
        if match:
            tags.append(match["value"].strip("\"'"))
    return tags


def set_new_tag(content: str, tag: str) -> str:
    """Cambia todos los `newTag` de la sección `images` por `tag` y devuelve el texto nuevo.

    Un cliente con dos imágenes (web y api) las publica juntas en la misma versión.
    """
    if not _TAG.fullmatch(tag):
        raise ValueError(f"La versión «{tag}» no es una etiqueta de imagen válida.")

    lines = content.splitlines(keepends=True)
    changed = 0
    for i in _images_block(lines):
        raw = lines[i]
        eol = raw[len(raw.rstrip("\r\n")):]
        match = _NEW_TAG.match(raw.rstrip("\r\n"))
        if not match:
            continue
        quoted = match["value"][0] in "\"'" or bool(_AMBIGUOUS.fullmatch(tag))
        value = f'"{tag}"' if quoted else tag
        lines[i] = f"{match['head']}{value}{match['tail']}{eol}"
        changed += 1
    if changed == 0:
        raise ValueError("El kustomization.yaml no tiene ningún «newTag» que cambiar.")
    return "".join(lines)
