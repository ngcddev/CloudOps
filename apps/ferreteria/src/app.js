// Lógica del sitio de El Tornillo (plantilla landing): muestra en el pie la versión que reporta /health.

const version = document.getElementById("version");

fetch("/health")
  .then((response) => response.json())
  .then((data) => {
    version.textContent = `Versión ${data.version}`;
    // La portada nueva aparece en toda versión posterior a la v1 (CSS: .solo-nueva-portada)
    document.body.dataset.version = data.version;
  })
  .catch(() => {
    // Sin servidor (por ejemplo, abriendo el archivo directo) se queda el texto por defecto.
  });
