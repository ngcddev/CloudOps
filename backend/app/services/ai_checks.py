# Controles de los textos del asistente antes de guardarlos o aprobarlos (spec 012, T03-T04).
import re

# Jerga que nunca llega al cliente (principio 8 y docs/glosario.md): los términos técnicos de la tabla
# «Traducción técnico → cliente» y las piezas de la plataforma. Se buscan como palabras completas, sin
# importar mayúsculas: «pod» se detecta, «podemos» no.
FORBIDDEN_TERMS = (
    "rollback",
    "revert",
    "incidente",
    "ticket",
    "mttr",
    "sla",
    "slo",
    "uptime",
    "latencia",
    "http",
    "5xx",
    "error 500",
    "despliegue",
    "deploy",
    "sync",
    "commit",
    "git",
    "gitops",
    "hub-gitops",
    "gitea",
    "argo",
    "argo cd",
    "kubernetes",
    "k3s",
    "clúster",
    "cluster",
    "namespace",
    "pod",
    "ingress",
    "docker",
    "contenedor",
    "prometheus",
    "grafana",
    "alertmanager",
    "loki",
    "gitleaks",
    "trivy",
    "cosign",
)

# Prioridades (P1-P4) y versiones de la app (v1, v2, v1.1): el cliente no las ve
_PATTERNS = [(term, re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.IGNORECASE)) for term in FORBIDDEN_TERMS]
_PATTERNS += [
    ("prioridad P1-P4", re.compile(r"(?<![\w-])p[1-4](?![\w-])", re.IGNORECASE)),
    ("versión vN", re.compile(r"(?<![\w-])v\d+(?:\.\d+)*(?![\w-])", re.IGNORECASE)),
]


def forbidden_terms(text: str) -> list[str]:
    """Términos prohibidos que aparecen en el texto, en el orden de la lista; vacía si el texto está limpio."""
    return [term for term, pattern in _PATTERNS if pattern.search(text)]


# Horas escritas como 14:00, 9:05 o 2:00 p. m. (el asistente puede usar cualquiera de las dos formas)
_TIME = re.compile(r"(?<![\d:])([01]?\d|2[0-3]):([0-5]\d)(?![\d:])(\s*([ap])\.?\s*m\.?)?", re.IGNORECASE)


def _as_24h(hours: int, minutes: int, meridiem: str | None) -> str:
    if meridiem is not None and hours <= 12:
        meridiem = meridiem.lower()
        if meridiem == "p" and hours != 12:
            hours += 12
        elif meridiem == "a" and hours == 12:
            hours = 0
    return f"{hours:02d}:{minutes:02d}"


def invented_times(text: str, facts: dict) -> list[str]:
    """Horas del texto (en formato 24 h) que no son ninguna hora real del incidente (`facts["times"]`)."""
    allowed = set(facts["times"])
    found = [_as_24h(int(h), int(m), mer or None) for h, m, _, mer in _TIME.findall(text)]
    return [time for time in dict.fromkeys(found) if time not in allowed]


def hours_match(text: str, facts: dict) -> bool:
    """True si toda hora que cita el texto es una hora del incidente (CA-2: sin datos inventados)."""
    return not invented_times(text, facts)
