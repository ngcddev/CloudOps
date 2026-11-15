# Prueba de Backstage en un Chromium real (spec 017, T02): el menú y el catálogo cargan sin errores de JavaScript, «Crear» ofrece la plantilla «Sitio de cliente»,
# la plantilla se ejecuta desde la interfaz y el componente aparece en el catálogo, y TechDocs muestra la documentación. Lo lanza backstage-ui.sh (Docker + Playwright).
from playwright.sync_api import sync_playwright

import os

BASE = "https://backstage.hub.local"
SLUG = os.environ.get("SLUG", "")
SALIDA = "/out"  # capturas de pantalla: se guardan aquí (carpeta montada por backstage-ui.sh)


def entrar_como_invitado(page):
    page.goto(BASE, wait_until="networkidle", timeout=60000)
    for texto in ("Enter", "ENTER", "Entrar"):
        boton = page.get_by_role("button", name=texto)
        if boton.count():
            boton.first.click()
            page.wait_for_load_state("networkidle")
            break


with sync_playwright() as p:
    navegador = p.chromium.launch(args=["--no-sandbox"])
    contexto = navegador.new_context(viewport={"width": 1400, "height": 900}, ignore_https_errors=True)
    page = contexto.new_page()
    errores = []
    page.on("pageerror", lambda e: errores.append(str(e)[:160]))
    entrar_como_invitado(page)
    page.screenshot(path=f"{SALIDA}/1-catalogo.png")
    print("catálogo:", page.title())

    page.goto(f"{BASE}/create", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f"{SALIDA}/2-crear.png")
    contenido = page.content()
    print("Crear muestra la plantilla:", "Sitio de cliente" in contenido)

    page.goto(f"{BASE}/create/templates/default/sitio-de-cliente", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    page.screenshot(path=f"{SALIDA}/3-formulario.png")
    print("formulario con el campo del nombre:", "Nombre del cliente en hub-gitops" in page.content())
    if SLUG:
        page.get_by_label("Nombre del cliente en hub-gitops").fill(SLUG)
        for nombre in ("Next", "Review", "Create"):
            boton = page.get_by_role("button", name=nombre)
            if boton.count():
                boton.first.click()
                page.wait_for_timeout(1500)
        # La tarea termina en un par de segundos; los enlaces de salida de la plantilla solo aparecen cuando terminó bien
        try:
            page.get_by_text("Abrir el sitio en el catálogo", exact=False).first.wait_for(timeout=45000)
            terminada = True
        except Exception:  # noqa: BLE001
            terminada = False
        page.screenshot(path=f"{SALIDA}/3b-tarea.png")
        print("tarea de la plantilla completada desde la interfaz:", terminada)
        page.goto(f"{BASE}/catalog/default/component/{SLUG}", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{SALIDA}/3c-componente.png")
        print("el componente registrado se abre en el catálogo:", "prueba desde la interfaz" in page.inner_text("body").lower())

    page.goto(f"{BASE}/docs/default/component/plataforma-cloudops", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)
    page.screenshot(path=f"{SALIDA}/4-docs.png")
    cuerpo = page.inner_text("body")
    print("TechDocs renderiza el contenido:", "Mapa de herramientas" in cuerpo or "Plataforma CloudOps Client Hub" in cuerpo)
    print("errores de JavaScript:", errores[:3] or "ninguno")
    navegador.close()
