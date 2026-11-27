// Crea un DOM de jsdom y lo deja como globales antes de cargar React (lo usa frontend/pruebas/error-boundary.sh).
const { JSDOM } = require("jsdom");
const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "http://localhost/" });
for (const clave of ["window", "document", "navigator", "HTMLElement", "Node", "MutationObserver", "Event", "MouseEvent"]) {
  Object.defineProperty(globalThis, clave, { value: dom.window[clave], configurable: true, writable: true });
}
