# Redacción de secretos (spec 020, T05; seguridad de la IA del módulo 5): antes de guardar un texto o de enviarlo a un modelo se tapan las claves, los tokens y las
# contraseñas que traiga. Una persona puede pegar un secreto en una pregunta, una nota o un registro sin darse cuenta; si queda en `ai_queries` o viaja en un prompt,
# deja de ser secreto. Es una red de seguridad de patrones conocidos, no una garantía: un secreto con un formato desconocido pasa.
import re
from collections.abc import Iterable

MARCA = "[SECRETO]"

# (nombre, patrón). Los de «clave = valor» conservan el nombre y tapan solo el valor.
_ASIGNACION = re.compile(
    r"(?i)\b((?:api[_-]?key|apikey|secret|token|passwd|password|contraseña|clave|credencial|authorization)\w*)(\s*[:=]\s*)(['\"]?)((?=[^\s'\",;]*\d)[^\s'\",;]{6,})\3"
)
_PATRONES = [
    ("clave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)")),
    ("clave de AWS", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token de GitHub", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("Bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("cadena de conexión", re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb|redis|amqp)://[^\s:@]+:[^\s@]+@[^\s]+")),
]


def redactar(texto: str) -> tuple[str, list[str]]:
    """El texto con los secretos tapados y los tipos que se encontraron (vacío si no había nada)."""
    if not texto:
        return texto, []
    encontrados: list[str] = []

    def tapar_asignacion(m: re.Match) -> str:
        encontrados.append("asignación de secreto")
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{MARCA}{m.group(3)}"

    resultado = _ASIGNACION.sub(tapar_asignacion, texto)
    for nombre, patron in _PATRONES:
        resultado, cuantos = patron.subn(MARCA, resultado)
        if cuantos:
            encontrados.append(nombre)
    return resultado, sorted(set(encontrados))


def redactar_todo(textos: Iterable[str]) -> tuple[list[str], list[str]]:
    """Redacta varios textos; devuelve los textos y la unión de los tipos encontrados."""
    salida, tipos = [], set()
    for texto in textos:
        limpio, encontrados = redactar(texto)
        salida.append(limpio)
        tipos.update(encontrados)
    return salida, sorted(tipos)
