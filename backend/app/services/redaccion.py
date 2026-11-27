# Redacción de secretos (spec 020, T05; seguridad de la IA del módulo 5): antes de guardar un texto o de enviarlo a un modelo se tapan las claves, los tokens y las
# contraseñas que traiga. Una persona puede pegar un secreto en una pregunta, una nota o un registro sin darse cuenta; si queda en `ai_queries` o viaja en un prompt,
# deja de ser secreto. Es una red de seguridad de patrones conocidos, no una garantía: un secreto con un formato desconocido pasa.
import re
from collections.abc import Iterable

MARK = "[SECRETO]"

# (nombre, patrón). Los de «clave = valor» conservan el nombre y tapan solo el valor.
_ASSIGNMENT = re.compile(
    r"(?i)\b((?:api[_-]?key|apikey|account[_-]?key|access[_-]?key|secret[_-]?key|private[_-]?key|shared[_-]?access[_-]?signature|sas[_-]?token|client[_-]?secret|secret|token|passwd|password|contraseña|clave|credencial|authorization)\w*)(\s*[:=]\s*)(['\"]?)((?=[^\s'\",;]*\d)[^\s'\",;]{6,})\3"
)
_PATTERNS = [
    ("clave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)")),
    ("clave de AWS", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token de GitHub", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("Bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("cadena de conexión", re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb|redis|amqp)://[^\s:@]+:[^\s@]+@[^\s]+")),
    # kubeconfig: certificados y claves en base64 (verificación del 15 nov)
    ("datos de kubeconfig", re.compile(r"(?i)\b(?:client-certificate-data|client-key-data|certificate-authority-data)\s*:\s*[A-Za-z0-9+/=]{16,}")),
]
# Una palabra de secreto seguida, en la misma frase, de una cadena larga mezclada (token de 40 hexadecimales, clave base64…): «token de gitea 5f2a…». Solo se tapa la cadena;
# sin la palabra clave cerca no se toca (un SHA de commit o un identificador largo en un texto normal no se confunde con un secreto).
_WORD_AND_STRING = re.compile(
    r"(?i)\b(?:token|clave|key|secret|secreto|contraseña|password|credencial)\b[^\n]{0,40}?\b((?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]{32,})\b"
)


def redact(texto: str) -> tuple[str, list[str]]:
    """El texto con los secretos tapados y los tipos que se encontraron (vacío si no había nada)."""
    if not texto:
        return texto, []
    encontrados: list[str] = []

    def mask_assignment(m: re.Match) -> str:
        encontrados.append("asignación de secreto")
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{MARK}{m.group(3)}"

    def mask_string(m: re.Match) -> str:
        encontrados.append("cadena larga junto a una palabra de secreto")
        return m.group(0).replace(m.group(1), MARK)

    resultado = _ASSIGNMENT.sub(mask_assignment, texto)
    resultado = _WORD_AND_STRING.sub(mask_string, resultado)
    for nombre, patron in _PATTERNS:
        resultado, cuantos = patron.subn(MARK, resultado)
        if cuantos:
            encontrados.append(nombre)
    return resultado, sorted(set(encontrados))


def redact_all(textos: Iterable[str]) -> tuple[list[str], list[str]]:
    """Redacta varios textos; devuelve los textos y la unión de los tipos encontrados."""
    salida, tipos = [], set()
    for texto in textos:
        limpio, encontrados = redact(texto)
        salida.append(limpio)
        tipos.update(encontrados)
    return salida, sorted(tipos)
