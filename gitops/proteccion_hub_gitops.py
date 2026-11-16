# Protección de archivos de hub-gitops en Gitea (spec 022, T13; auditoría K8-05): el Hub (`hub-bot`) solo puede cambiar lo que escribe, los archivos de cada
# cliente (kustomization.yaml, catalog-info.yaml y backend.yaml); observability/, hub/, platform/ y clients/_base los cambia el equipo con `forja-admin`.
# Sin esto, un token de `hub-bot` robado o mal usado escribiría un ClusterRoleBinding en observability/ y Argo CD lo aplicaría con el proyecto `default`.
#
# Es una regla de protección de la rama `main`: solo el administrador empuja libremente (lo que necesita sincronizar-hub-gitops.sh); a los demás Gitea les
# deja cambiar únicamente lo que coincide con PATRONES_DEL_HUB. Se probó con un repositorio y un usuario desechables (gitops/pruebas/proteccion_hub_gitops.py).
#
# Uso:  GITEA_USER=... GITEA_PASSWORD=... python gitops/proteccion_hub_gitops.py --aplicar | --comprobar
#   --aplicar     crea la regla o la deja como debe (se puede repetir sin efecto)
#   --comprobar   no cambia nada; sale con 1 si la regla falta o es distinta
# Variables: GITEA_URL (http://gitea.hub.local), ORG (forja-digital), REPO (hub-gitops), RAMA (main). Con `set -a; . ./.env.cluster; set +a` el usuario y la clave
# salen de GITEA_ADMIN_USER y GITEA_ADMIN_PASSWORD.
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

# Lo único que escribe el Hub: clients/<cliente>/<archivo>. Gitea compara con glob: `*` no cruza `/`, `**` sí.
PATRONES_DEL_HUB = ["clients/*/kustomization.yaml", "clients/*/catalog-info.yaml", "clients/*/backend.yaml"]


def regla(administrador: str, rama: str = "main") -> dict:
    """La regla de protección que se aplica: solo `administrador` empuja libremente; los demás, solo a PATRONES_DEL_HUB."""
    return {
        "rule_name": rama,
        "branch_name": rama,
        "enable_push": True,
        "enable_push_whitelist": True,
        "push_whitelist_usernames": [administrador],
        "unprotected_file_patterns": ";".join(PATRONES_DEL_HUB),
    }


def coincide(patron: str, ruta: str) -> bool:
    """Glob como el de Gitea: `**` cruza carpetas y `*` no cruza `/`."""
    expresion = re.escape(patron).replace(r"\*\*", "\0").replace(r"\*", "[^/]*").replace("\0", ".*")
    return re.fullmatch(expresion, ruta) is not None


def lo_puede_cambiar_el_hub(ruta: str) -> bool:
    return any(coincide(patron, ruta) for patron in PATRONES_DEL_HUB)


class Gitea:
    def __init__(self, url: str, usuario: str, clave: str):
        self.url = url.rstrip("/") + "/api/v1"
        self.autorizacion = "Basic " + base64.b64encode(f"{usuario}:{clave}".encode()).decode()

    def llamar(self, metodo: str, ruta: str, cuerpo: dict | None = None) -> tuple[int, object]:
        pedido = urllib.request.Request(self.url + ruta, method=metodo, data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
        pedido.add_header("Content-Type", "application/json")
        pedido.add_header("Authorization", self.autorizacion)
        try:
            with urllib.request.urlopen(pedido, timeout=20) as respuesta:
                texto = respuesta.read().decode()
                return respuesta.status, (json.loads(texto) if texto else None)
        except urllib.error.HTTPError as error:
            texto = error.read().decode()
            try:
                return error.code, json.loads(texto)
            except ValueError:
                return error.code, texto


def diferencias(actual: dict, esperada: dict) -> list[str]:
    """Qué campos de la regla que hay en Gitea no son los esperados."""
    problemas = []
    for campo in ("enable_push", "enable_push_whitelist", "push_whitelist_usernames", "unprotected_file_patterns"):
        if actual.get(campo) != esperada[campo]:
            problemas.append(f"{campo}: hay {actual.get(campo)!r} y debe ser {esperada[campo]!r}")
    # Gitea 1.22 no expone un campo para forzar empujes: con la regla puesta, `git push --force` a main se rechaza para todos (lo comprueba la prueba)
    return problemas


def aplicar(gitea: Gitea, org: str, repo: str, esperada: dict) -> str:
    base = f"/repos/{org}/{repo}/branch_protections"
    estado, actual = gitea.llamar("GET", f"{base}/{esperada['rule_name']}")
    if estado == 404:
        estado, respuesta = gitea.llamar("POST", base, esperada)
        if estado != 201:
            raise SystemExit(f"No se pudo crear la regla: {estado} {respuesta}")
        return "creada"
    if estado != 200:
        raise SystemExit(f"No se pudo leer la regla: {estado} {actual}")
    if not diferencias(actual, esperada):
        return "ya estaba como debe"
    estado, respuesta = gitea.llamar("PATCH", f"{base}/{esperada['rule_name']}", esperada)
    if estado != 200:
        raise SystemExit(f"No se pudo actualizar la regla: {estado} {respuesta}")
    return "actualizada"


def main(argumentos: list[str]) -> int:
    if len(argumentos) != 1 or argumentos[0] not in ("--aplicar", "--comprobar"):
        print(__doc__.split("Uso:")[1].split("\n#   --aplicar")[0].strip(), file=sys.stderr)
        return 2
    usuario, clave = os.environ.get("GITEA_USER"), os.environ.get("GITEA_PASSWORD")
    if not usuario or not clave:
        print("Falta GITEA_USER o GITEA_PASSWORD (el administrador de Gitea).", file=sys.stderr)
        return 2
    org, repo, rama = os.environ.get("ORG", "forja-digital"), os.environ.get("REPO", "hub-gitops"), os.environ.get("RAMA", "main")
    gitea = Gitea(os.environ.get("GITEA_URL", "http://gitea.hub.local"), usuario, clave)
    esperada = regla(usuario, rama)
    if argumentos[0] == "--aplicar":
        print(f"{org}/{repo}, rama {rama}: regla {aplicar(gitea, org, repo, esperada)}")
        return 0
    estado, actual = gitea.llamar("GET", f"/repos/{org}/{repo}/branch_protections/{rama}")
    if estado == 404:
        print(f"{org}/{repo}, rama {rama}: SIN regla de protección: hub-bot puede escribir en todo el repositorio.")
        return 1
    problemas = diferencias(actual, esperada) if estado == 200 else [f"no se pudo leer la regla ({estado})"]
    for problema in problemas:
        print(f"  ✗ {problema}")
    print(f"{org}/{repo}, rama {rama}: " + ("regla distinta de la esperada" if problemas else "regla correcta"))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
