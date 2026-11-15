# Prueba de la voz del asistente en un Chromium real (spec 021, T03): con un micrófono FALSO que reproduce un audio de práctica, se pulsa «Hablar», se detiene, se comprueba que la
# transcripción llega al cuadro de la pregunta, se envía y se comprueba que la respuesta se lee en voz alta. Lo lanza voz-ui.sh (Docker + Playwright).
import os
import socket
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ["HUB_WEB"]  # un nombre *.localhost: Chromium lo trata como contexto seguro y deja usar el micrófono sin HTTPS
IP_ANFITRION = socket.gethostbyname("host.docker.internal")
SALIDA = "/out"
fallos = 0


def comprobar(ok: bool, texto: str) -> None:
    global fallos
    print(("   OK   " if ok else "   FALLA ") + texto, flush=True)
    fallos += 0 if ok else 1


with sync_playwright() as p:
    navegador = p.chromium.launch(args=[
        "--no-sandbox", f"--host-resolver-rules=MAP hub.localhost {IP_ANFITRION}", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
        "--use-file-for-fake-audio-capture=/out/audio-de-practica.wav",
    ])
    contexto = navegador.new_context(viewport={"width": 1280, "height": 900}, permissions=["microphone"])
    page = contexto.new_page()
    errores = []
    page.on("pageerror", lambda e: errores.append(str(e)[:160]))
    # El navegador de pruebas no tiene altavoz: se cuenta cuántas veces el Hub pide reproducir audio
    page.add_init_script("window.__reproducciones = 0; const p = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { window.__reproducciones++; return p.call(this); };")

    page.goto(BASE, wait_until="networkidle", timeout=60000)
    page.get_by_label("Correo").fill(os.environ["HUB_USUARIO"])
    page.get_by_label("Contraseña").fill(os.environ["HUB_PASSWORD"])
    page.get_by_role("button", name="Entrar").click()
    page.wait_for_load_state("networkidle")
    # La sesión vive en memoria: se navega por el menú, no con una recarga completa
    page.get_by_role("link", name="Asistente").first.click()
    page.wait_for_load_state("networkidle")

    boton = page.get_by_role("button", name="Hablar")
    try:
        boton.wait_for(timeout=15000)
    except Exception:  # noqa: BLE001
        page.screenshot(path=f"{SALIDA}/0-sin-boton.png")
        print("   texto de la página:", " | ".join(page.inner_text("body")[:400].splitlines()), "| url:", page.url)
        raise
    comprobar(boton.is_visible(), "el botón «Hablar» aparece (el servicio de voz responde y el navegador da micrófono)")
    page.screenshot(path=f"{SALIDA}/1-asistente.png")

    boton.click()
    detener = page.get_by_role("button", name="Detener")
    detener.wait_for(timeout=10000)
    comprobar(detener.is_visible(), "al pulsar «Hablar» queda escuchando y ofrece «Detener»")
    page.wait_for_timeout(9000)  # el audio de práctica dura ~8 s
    page.screenshot(path=f"{SALIDA}/2-escuchando.png")
    detener.click()

    cuadro = page.get_by_label("Tu pregunta")
    page.wait_for_function("document.querySelector('.assistant-form input').value.length > 5", timeout=60000)
    texto = cuadro.input_value()
    print(f"   transcripción: {texto!r}")
    comprobar("cambio" in texto.lower() and "aprobar" in texto.lower().replace("probar", "aprobar"), "la transcripción llega al cuadro de la pregunta y se puede corregir")
    page.screenshot(path=f"{SALIDA}/3-transcrito.png")

    cuadro.fill("¿Cómo apruebo un cambio de versión?")
    page.get_by_role("button", name="Preguntar").click()
    page.locator(".assistant-answer").first.wait_for(timeout=90000)
    respuesta = page.locator(".assistant-answer").first.inner_text()
    print(f"   respuesta: {respuesta[:140]!r}")
    comprobar(len(respuesta) > 10, "el asistente responde por escrito")
    page.wait_for_function("window.__reproducciones > 0", timeout=60000)
    comprobar(page.evaluate("window.__reproducciones") > 0, "la respuesta se lee en voz alta (el Hub pidió reproducir el audio)")
    page.screenshot(path=f"{SALIDA}/4-respuesta.png")

    page.get_by_label("Leer las respuestas en voz alta").uncheck()
    comprobar(page.evaluate("window.localStorage.getItem('asistente.leerRespuestas')") == "no", "la preferencia de no leer en voz alta se recuerda")
    comprobar(not errores, f"sin errores de JavaScript {errores[:2] if errores else ''}")
    navegador.close()

print("OK" if fallos == 0 else f"{fallos} comprobación(es) fallaron")
sys.exit(1 if fallos else 0)
