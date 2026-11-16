// Fija el tema antes de pintar: el que la persona eligió, o el del sistema.
// Está en un archivo y no en línea en index.html porque la Content-Security-Policy de nginx (frontend/seguridad.conf) no permite scripts en línea (auditoría CT-13).
(function () {
  var theme = null;
  try {
    theme = localStorage.getItem("hub.theme");
  } catch (e) {}
  if (theme !== "light" && theme !== "dark") {
    theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = theme;
})();
