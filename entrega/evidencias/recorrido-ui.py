# Recorrido de la interfaz con un navegador real (Playwright en contenedor): entra al Hub como la agencia y como un cliente del portal, y abre las pantallas de Argo CD, Grafana, MLflow y Gitea
# para dejar capturas numeradas que sirven de anexos. El Hub guarda la sesión solo en memoria, así que se navega con los enlaces del menú (un goto a otra ruta pierde la sesión). Registra por
# pantalla si el contenido esperado aparece; sale con error si alguna falla. Variables: HUB_USER, HUB_PW, CLIENTE_USER, CLIENTE_PW, GRAFANA_PW, ARGO_PW (por el entorno, nunca en archivos).
import json
import os
import sys

from playwright.sync_api import sync_playwright

OUT = "/out"
indice, errores_js = [], []
fallas = 0


def captura(page, nombre, esperado=None, espera=1500):
    global fallas
    page.wait_for_timeout(espera)
    page.screenshot(path=f"{OUT}/{nombre}.png", full_page=True)
    texto = page.inner_text("body")[:8000] if page.query_selector("body") else ""
    ok = esperado is None or esperado.lower() in texto.lower()
    fallas += 0 if ok else 1
    indice.append({"captura": f"{nombre}.png", "url": page.url, "titulo": page.title(), "contiene_esperado": ok, "esperado": esperado})
    print(("OK   " if ok else "FALLA"), nombre, "|", page.url[:60], "| esperado:", esperado, flush=True)


def ir(page, url, nombre, esperado=None, espera=1500):
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception as e:  # noqa: BLE001
        print("AVISO", nombre, str(e)[:120], flush=True)
    captura(page, nombre, esperado, espera)


def menu(page, etiqueta, nombre, esperado=None, espera=1500):
    try:
        page.get_by_role("link", name=etiqueta, exact=True).first.click(timeout=15000)
        page.wait_for_load_state("networkidle")
    except Exception as e:  # noqa: BLE001
        print("AVISO menú", etiqueta, str(e)[:100], flush=True)
    captura(page, nombre, esperado, espera)


def entrar_hub(nav, usuario, clave):
    ctx = contexto(nav)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errores_js.append(str(e)[:160]))
    page.goto("https://hub.local/login", wait_until="networkidle", timeout=60000)
    page.fill("input[type=email]", usuario)
    page.fill("input[type=password]", clave)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    return ctx, page


def contexto(nav):
    # locale: sin él el Chromium del contenedor no tiene idioma y Grafana falla con «Incorrect locale information provided» (Intl.NumberFormat)
    return nav.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True, locale="es-CO", timezone_id="America/Bogota")


with sync_playwright() as p:
    nav = p.chromium.launch(args=["--no-sandbox"])

    # ---- Hub: agencia ----
    ctx = contexto(nav)
    page = ctx.new_page()
    page.goto("https://hub.local/login", wait_until="networkidle", timeout=60000)
    captura(page, "E01-login", "Contraseña")
    ctx.close()
    ctx, page = entrar_hub(nav, os.environ["HUB_USER"], os.environ["HUB_PW"])
    captura(page, "E02-agencia-inicio", "La Sazón")
    menu(page, "Clientes", "E03-agencia-clientes", "La Sazón")
    try:
        page.get_by_role("link", name="La Sazón").first.click(timeout=10000)
        page.wait_for_load_state("networkidle")
    except Exception as e:  # noqa: BLE001
        print("AVISO abrir cliente", str(e)[:100], flush=True)
    captura(page, "E04-agencia-cliente", "La Sazón")
    # La pantalla de métricas no tiene enlace desde el detalle: se abre con el enrutador del propio sitio (pushState + popstate) para no perder la sesión
    page.evaluate("window.history.pushState({}, '', '/agencia/clientes/1/metricas'); window.dispatchEvent(new PopStateEvent('popstate'))")
    page.wait_for_load_state("networkidle")
    captura(page, "E05-agencia-metricas", "isponibilidad", espera=4000)
    for etiqueta, nombre, esperado in [
        ("Solicitudes", "E06-agencia-solicitudes", None),
        ("Cambios", "E07-agencia-cambios", "ambio"),
        ("Servicios", "E08-agencia-servicios", "restaurante"),
        ("Incidentes", "E09-agencia-incidentes", "ncidente"),
        ("Asistente", "E11-agencia-asistente", "sistente"),
        ("Reportes", "E10-agencia-reportes", "eporte"),
        ("Bitácora", "E12-agencia-bitacora", "itácora"),
    ]:
        menu(page, etiqueta, nombre, esperado)
    ctx.close()

    # ---- Hub: portal del cliente ----
    ctx, page = entrar_hub(nav, os.environ["CLIENTE_USER"], os.environ["CLIENTE_PW"])
    captura(page, "E13-portal-inicio", "Su sitio")
    menu(page, "Solicitudes", "E14-portal-solicitudes", None)
    menu(page, "Reportes", "E15-portal-reportes", "eporte")
    ctx.close()

    # ---- Argo CD ----
    ctx = contexto(nav)
    page = ctx.new_page()
    try:
        page.goto("https://argocd.hub.local/login", wait_until="networkidle", timeout=60000)
        page.locator("input").first.fill("admin")
        page.locator("input[type=password]").fill(os.environ["ARGO_PW"])
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
    except Exception as e:  # noqa: BLE001
        print("AVISO login Argo CD:", str(e)[:120], flush=True)
    ir(page, "https://argocd.hub.local/applications", "E20-argocd-aplicaciones", "cliente-restaurante", espera=4000)
    ir(page, "https://argocd.hub.local/applications/argocd/cliente-restaurante", "E21-argocd-cliente-restaurante", "restaurante", espera=5000)
    ctx.close()

    # ---- Grafana (por HTTP: por HTTPS el navegador de pruebas no cargaba sus archivos) ----
    ctx = contexto(nav)
    page = ctx.new_page()
    try:
        page.goto("http://grafana.hub.local/login", wait_until="networkidle", timeout=60000)
        page.locator("input").first.fill("admin")
        page.locator("input[type=password]").fill(os.environ["GRAFANA_PW"])
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
    except Exception as e:  # noqa: BLE001
        print("AVISO login Grafana:", str(e)[:120], flush=True)
    ir(page, "http://grafana.hub.local/dashboards", "E30-grafana-tableros", "ashboard", espera=4000)
    try:
        page.get_by_text("CloudOps", exact=True).first.click(timeout=8000)  # abre la carpeta de tableros
        page.wait_for_timeout(2000)
        page.locator("a[href*='/d/']").first.click(timeout=10000)
        page.wait_for_load_state("networkidle")
        captura(page, "E31-grafana-tablero", None, espera=8000)
    except Exception as e:  # noqa: BLE001
        print("AVISO abrir un tablero:", str(e)[:100], flush=True)
        fallas += 1
    ctx.close()

    # ---- MLflow y Gitea (sin sesión) ----
    ctx = contexto(nav)
    page = ctx.new_page()
    ir(page, "https://mlflow.hub.local/#/models", "E40-mlflow-modelos", "compuerta", espera=4000)
    ir(page, "http://gitea.hub.local/forja-digital/hub-gitops", "E41-gitea-hub-gitops", "hub-gitops")
    ir(page, "http://gitea.hub.local/forja-digital/ferreteria/actions", "E42-gitea-puerta-ferreteria", "ferreteria")
    ctx.close()
    nav.close()

json.dump({"capturas": indice, "errores_javascript_hub": errores_js}, open(f"{OUT}/indice.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("errores de JavaScript en el Hub:", len(errores_js), errores_js[:3])
print("pantallas con contenido inesperado:", fallas)
sys.exit(1 if fallas or errores_js else 0)
