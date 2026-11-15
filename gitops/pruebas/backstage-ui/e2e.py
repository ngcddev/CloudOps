# Orquesta la prueba de Backstage desde el navegador (spec 017, T02): el Hub deja un catalog-info temporal en hub-gitops, navegador.py ejecuta la plantilla desde la interfaz y se limpia todo
# (la entidad registrada y el archivo). Variables: GITEA_ADMIN_USER y GITEA_ADMIN_PASSWORD (.env.cluster) y SALIDA (carpeta de las capturas).
import base64
import http.client
import json
import os
import ssl
import subprocess
import urllib.request
import urllib.error

AUTH = base64.b64encode(f"{os.environ['GITEA_ADMIN_USER']}:{os.environ['GITEA_ADMIN_PASSWORD']}".encode()).decode()
SLUG = "prueba-ui"
RUTA = f"clients/{SLUG}/catalog-info.yaml"
CAT = (
    "apiVersion: backstage.io/v1alpha1\nkind: Component\nmetadata:\n  name: "
    + SLUG
    + "\n  title: Prueba desde la interfaz\nspec:\n  type: website\n  lifecycle: experimental\n  owner: forja-digital\n"
)


def llamar(host, metodo, ruta, cuerpo=None, auth=False):
    cab = {"Host": host, "Content-Type": "application/json"}
    if auth:
        cab["Authorization"] = "Basic " + AUTH
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    if host.startswith("backstage"):
        # Backstage solo se publica por HTTPS (certificado autofirmado de Traefik): se entra por 443 con el encabezado Host
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
        con = http.client.HTTPSConnection("127.0.0.1", 443, context=contexto, timeout=60)
        con.request(metodo, ruta, datos, cab)
        r = con.getresponse()
        crudo = r.read()
        try:
            return r.status, json.loads(crudo or b"null")
        except ValueError:
            return r.status, None
    req = urllib.request.Request("http://127.0.0.1" + ruta, datos, cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, None


def g(m, r, c=None):
    return llamar("gitea.hub.local", m, "/api/v1/repos/forja-digital/hub-gitops/contents/" + r, c, True)


print(
    "catalog-info temporal:",
    g(
        "POST",
        RUTA,
        {"content": base64.b64encode(CAT.encode()).decode(), "message": "test(017): temporal de la prueba de interfaz", "branch": "main"},
    )[0],
)
try:
    sp = os.environ["SALIDA"]
    r = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--add-host",
            "backstage.hub.local:172.30.0.1",
            "-e",
            f"SLUG={SLUG}",
            "-v",
            f"{sp}:/out",
            "mcr.microsoft.com/playwright/python:v1.49.1-noble",
            "sh",
            "-c",
            "pip install -q playwright==1.49.1 >/dev/null 2>&1; python /out/navegador.py",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    print(r.stdout[-1500:], r.stderr[-400:])
finally:
    for loc in llamar("backstage.hub.local", "GET", "/api/catalog/locations")[1] or []:
        if isinstance(loc, dict) and loc["data"]["target"].endswith(RUTA):
            print("limpieza location:", llamar("backstage.hub.local", "DELETE", "/api/catalog/locations/" + loc["data"]["id"])[0])
    c, f = g("GET", RUTA + "?ref=main")
    if c == 200:
        print("limpieza archivo:", g("DELETE", RUTA, {"sha": f["sha"], "message": "test(017): quitar temporal", "branch": "main"})[0])
