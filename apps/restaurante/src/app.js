// Lógica del sitio de La Sazón (plantilla landing): muestra en el pie la versión que reporta /health.

const version = document.getElementById("version");

fetch("/health")
  .then((response) => response.json())
  .then((data) => {
    version.textContent = `Versión ${data.version}`;
  })
  .catch(() => {
    // Sin servidor (por ejemplo, abriendo el archivo directo) se queda el texto por defecto.
  });
