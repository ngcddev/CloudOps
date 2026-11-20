# Capturas para los apéndices B y C del informe final (Playwright en contenedor): aplicaciones de Argo CD, los dos tableros de Grafana
# en la ventana de la corrida (rollback C25 y caída cronometrada C26, 16 y 17 nov 2026) y el modelo de la compuerta en MLflow.
# Espera a que Grafana dibuje los paneles antes de capturar. Variables: GRAFANA_PW y ARGO_PW (por el entorno, nunca en archivos).
import os

from playwright.sync_api import sync_playwright

OUT = "/out"
# Ventana de la corrida en milisegundos UTC: 2026-11-16 22:50 a 2026-11-17 01:50 (hora de Bogotá: 17:50 a 20:50).
DESDE, HASTA = 1794869400000, 1794880200000
estado = []


def guardar(page, nombre, espera=3000, completa=True):
    page.wait_for_timeout(espera)
    page.screenshot(path=f"{OUT}/{nombre}.png", full_page=completa)
    estado.append(f"OK {nombre} {page.url}")
    print(estado[-1], flush=True)


def entrar(page, url, clave):
    page.goto(url, wait_until="load", timeout=60000)
    page.locator("input").first.fill("admin")
    page.locator("input[type=password]").fill(clave)
    page.keyboard.press("Enter")
    page.wait_for_timeout(5000)


with sync_playwright() as p:
    nav = p.chromium.launch()
    ctx = nav.new_context(ignore_https_errors=True, viewport={"width": 1600, "height": 1000}, locale="en-US",  # con es-CO Grafana no arranca en el Chromium del contenedor (RangeError de Intl)
                          timezone_id="America/Bogota", color_scheme="light")
    page = ctx.new_page()

    # Argo CD: lista de aplicaciones (Figura 16)
    entrar(page, "https://argocd.hub.local/login", os.environ["ARGO_PW"])
    page.goto("https://argocd.hub.local/applications?view=list", wait_until="domcontentloaded", timeout=60000)
    page.get_by_text("cliente-restaurante").first.wait_for(timeout=30000)
    guardar(page, "F16-argocd-aplicaciones", 4000)

    # Grafana: tableros en la ventana de la corrida (Figuras 17 y 18), con el tema por defecto (el modo kiosco con tema claro deja los paneles en blanco)
    entrar(page, "http://grafana.hub.local/login", os.environ["GRAFANA_PW"])
    page.set_viewport_size({"width": 1600, "height": 2100})  # ventana alta: la captura de página completa deja la cuadrícula en blanco
    for uid, nombre in (("servicio-sitios", "F17-grafana-servicio-sitios"), ("red-use", "F18-grafana-red-use")):
        page.goto(f"http://grafana.hub.local/d/{uid}?orgId=1&from={DESDE}&to={HASTA}&timezone=America%2FBogota",
                  wait_until="load", timeout=90000)
        page.locator("[data-viz-panel-key], .react-grid-item").first.wait_for(timeout=60000)
        page.get_by_text("Cómo leer este tablero").first.wait_for(timeout=60000)
        guardar(page, nombre, 15000, completa=False)  # 15 s para que terminen las consultas a Prometheus

    page.set_viewport_size({"width": 1600, "height": 1000})
    # MLflow: modelo registrado de la compuerta con su alias (Figura 19)
    page.goto("https://mlflow.hub.local/#/models/compuerta-asistente", wait_until="load", timeout=60000)
    page.get_by_text("compuerta-asistente").first.wait_for(timeout=30000)
    guardar(page, "F19-mlflow-compuerta", 4000)
    nav.close()

with open(f"{OUT}/capturas.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(estado) + "\n")
