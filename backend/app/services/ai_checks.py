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
