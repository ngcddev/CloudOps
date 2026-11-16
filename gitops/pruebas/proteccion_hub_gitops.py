# Prueba de la protección de hub-gitops (spec 022, T13; auditoría K8-05) en un repositorio y un usuario desechables de Gitea: no toca hub-gitops.
# Comprueba, con la misma regla que aplica gitops/proteccion_hub_gitops.py, que el bot (colaborador con escritura, como `hub-bot`) solo puede cambiar lo que
# escribe el Hub y que el administrador sigue pudiendo con todo, tanto por la API de contenidos (la que usa el Hub) como por `git push` (la que usa
# sincronizar-hub-gitops.sh). Antes de proteger confirma el riesgo: el bot escribe en observability/.
# Uso:  set -a; . ./.env.cluster; set +a; GITEA_USER=$GITEA_ADMIN_USER GITEA_PASSWORD=$GITEA_ADMIN_PASSWORD python gitops/pruebas/proteccion_hub_gitops.py
import base64
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proteccion_hub_gitops import Gitea, aplicar, lo_puede_cambiar_el_hub, regla  # noqa: E402

URL = os.environ.get("GITEA_URL", "http://gitea.hub.local")
ORG, REPO, BOT = os.environ.get("ORG", "forja-digital"), "proteccion-prueba", "proteccion-bot"
ADMIN = (os.environ.get("GITEA_USER", ""), os.environ.get("GITEA_PASSWORD", ""))
if not all(ADMIN):
    sys.exit("Falta GITEA_USER o GITEA_PASSWORD (el administrador de Gitea).")
CLAVE_BOT = secrets.token_urlsafe(18)
fallos: list[str] = []


def verificar(titulo: str, permitido: bool, esperado: bool, detalle: str = "") -> None:
    correcto = permitido == esperado
    print(f"  {'✓' if correcto else '✗'} {titulo:<66} → {'permitido' if permitido else 'rechazado'}" + ("" if permitido or not detalle else f"  [{detalle}]"))
    if not correcto:
        fallos.append(titulo)


def escribir(cliente: Gitea, ruta: str) -> tuple[bool, str]:
    """Escribe con la API de contenidos de Gitea, como hace el Hub."""
    estado, actual = cliente.llamar("GET", f"/repos/{ORG}/{REPO}/contents/{ruta}?ref=main")
    cuerpo = {"content": base64.b64encode(b"cambio\n").decode(), "message": "prueba", "branch": "main"}
    if estado == 200:
        estado, respuesta = cliente.llamar("PUT", f"/repos/{ORG}/{REPO}/contents/{ruta}", {**cuerpo, "sha": actual["sha"]})
    else:
        estado, respuesta = cliente.llamar("POST", f"/repos/{ORG}/{REPO}/contents/{ruta}", cuerpo)
    return estado in (200, 201), (respuesta.get("message", "") if isinstance(respuesta, dict) else str(respuesta))[:80]


def empujar(usuario: str, clave: str, ruta: str) -> tuple[bool, str]:
    """Escribe con `git push` por HTTP, como hace sincronizar-hub-gitops.sh."""
    carpeta = tempfile.mkdtemp()
    try:
        host = URL.split("://", 1)[1]
        git = lambda *a: subprocess.run(["git", "-C", carpeta, *a], capture_output=True, text=True)  # noqa: E731
        subprocess.run(["git", "clone", "-q", f"http://{usuario}:{clave}@{host}/{ORG}/{REPO}.git", carpeta], capture_output=True, text=True)
        git("config", "user.name", usuario)
        git("config", "user.email", f"{usuario}@forja.test")
        destino = Path(carpeta, ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, "a", encoding="utf-8") as archivo:
            archivo.write("cambio por git\n")
        git("add", "-A")
        git("commit", "-q", "-m", "prueba por git")
        resultado = git("push", "-q", "origin", "HEAD:main")
        return resultado.returncode == 0, "git rechazó el push" if resultado.returncode else ""
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def reescribir_historia(usuario: str, clave: str) -> bool:
    """Intenta reescribir la historia de `main` con `git push --force` (quita el último commit y pone otro distinto)."""
    carpeta = tempfile.mkdtemp()
    try:
        host = URL.split("://", 1)[1]
        git = lambda *a: subprocess.run(["git", "-C", carpeta, *a], capture_output=True, text=True)  # noqa: E731
        subprocess.run(["git", "clone", "-q", f"http://{usuario}:{clave}@{host}/{ORG}/{REPO}.git", carpeta], capture_output=True, text=True)
        git("config", "user.name", usuario)
        git("config", "user.email", f"{usuario}@forja.test")
        git("reset", "-q", "--hard", "HEAD~1")
        Path(carpeta, "clients", "ferreteria").mkdir(parents=True, exist_ok=True)
        Path(carpeta, "clients", "ferreteria", "kustomization.yaml").write_text("historia reescrita\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "historia reescrita")
        return git("push", "-q", "--force", "origin", "HEAD:main").returncode == 0
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


admin = Gitea(URL, *ADMIN)
bot = Gitea(URL, BOT, CLAVE_BOT)
try:
    admin.llamar("DELETE", f"/repos/{ORG}/{REPO}")
    admin.llamar("DELETE", f"/admin/users/{BOT}?purge=true")
    estado, r = admin.llamar("POST", "/admin/users", {"username": BOT, "email": f"{BOT}@forja.test", "password": CLAVE_BOT, "must_change_password": False})
    assert estado == 201, f"no se pudo crear el usuario de prueba: {estado} {r}"
    estado, r = admin.llamar("POST", f"/orgs/{ORG}/repos", {"name": REPO, "auto_init": True, "default_branch": "main", "private": False})
    assert estado == 201, f"no se pudo crear el repositorio de prueba: {estado} {r}"
    estado, r = admin.llamar("PUT", f"/repos/{ORG}/{REPO}/collaborators/{BOT}", {"permission": "write"})
    assert estado == 204, f"no se pudo dar escritura al usuario de prueba: {estado} {r}"
    for ruta in ("observability/a.txt", "hub/a.txt", "platform/a.txt", "clients/_base/a.txt", "clients/ferreteria/kustomization.yaml"):
        assert escribir(admin, ruta)[0], f"no se pudo crear {ruta}"

    print("\nSin protección (como estaba hub-gitops):")
    verificar("el bot escribe observability/ por la API", escribir(bot, "observability/a.txt")[0], True)

    print(f"\nCon la regla de gitops/proteccion_hub_gitops.py ({aplicar(admin, ORG, REPO, regla(ADMIN[0]))}):")
    for ruta in ("observability/a.txt", "hub/a.txt", "platform/a.txt", "clients/_base/a.txt"):
        permitido, detalle = escribir(bot, ruta)
        verificar(f"bot · API de contenidos · {ruta}", permitido, False, detalle)
    for ruta in ("clients/ferreteria/kustomization.yaml", "clients/nuevo/catalog-info.yaml", "clients/nuevo/backend.yaml", "clients/nuevo/kustomization.yaml"):
        verificar(f"bot · API de contenidos · {ruta}", escribir(bot, ruta)[0], True)
    verificar("bot · git push · observability/b.txt", *empujar(BOT, CLAVE_BOT, "observability/b.txt")[:1], False)
    verificar("bot · git push · clients/ferreteria/kustomization.yaml", empujar(BOT, CLAVE_BOT, "clients/ferreteria/kustomization.yaml")[0], True)
    for ruta in ("observability/a.txt", "hub/a.txt", "platform/a.txt", "clients/_base/a.txt"):
        verificar(f"administrador · API de contenidos · {ruta}", escribir(admin, ruta)[0], True)
    for ruta in ("observability/c.txt", "hub/c.txt", "platform/c.txt", "clients/_base/c.txt"):
        verificar(f"administrador · git push · {ruta}", empujar(ADMIN[0], ADMIN[1], ruta)[0], True)

    print("\nReescribir la historia de main con `git push --force`:")
    forzado_del_bot = reescribir_historia(BOT, CLAVE_BOT)
    forzado_del_admin = reescribir_historia(ADMIN[0], ADMIN[1])
    print(f"  · el bot  → {'permitido' if forzado_del_bot else 'rechazado'}\n  · el administrador → {'permitido' if forzado_del_admin else 'rechazado'}")
    verificar("bot · git push --force", forzado_del_bot, False)
    verificar("administrador · git push --force (nadie reescribe la historia de main)", forzado_del_admin, False)

    print("\nLímite conocido (no es un fallo de la regla): `clients/*/kustomization.yaml` también coincide con clients/_base/kustomization.yaml, así que el bot puede")
    print("cambiarlo; sus efectos los acota el proyecto `clientes` de Argo CD (solo namespaces cliente-* y los tipos de recurso de un sitio).")
    verificar("bot · API de contenidos · clients/_base/kustomization.yaml (hoy permitido)", escribir(bot, "clients/_base/kustomization.yaml")[0], True)

    print("\nLa lista de PATRONES_DEL_HUB y las rutas:")
    verificar("coincide clients/ferreteria/kustomization.yaml", lo_puede_cambiar_el_hub("clients/ferreteria/kustomization.yaml"), True)
    verificar("no coincide observability/prometheus/prometheus.yml", lo_puede_cambiar_el_hub("observability/prometheus/prometheus.yml"), False)
    verificar("no coincide clients/a/b/kustomization.yaml (`*` no cruza carpetas)", lo_puede_cambiar_el_hub("clients/a/b/kustomization.yaml"), False)
finally:
    admin.llamar("DELETE", f"/repos/{ORG}/{REPO}")
    admin.llamar("DELETE", f"/admin/users/{BOT}?purge=true")
    print("\n(repositorio y usuario de prueba borrados)")
print("\nTODO EN VERDE" if not fallos else f"\nFALLÓ: {len(fallos)} comprobación(es)")
sys.exit(1 if fallos else 0)
