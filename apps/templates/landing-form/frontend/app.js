// Lógica de la plantilla landing-form: envía el formulario a /api/contact y muestra la versión del sitio.

const form = document.getElementById("contact-form");
const message = document.getElementById("form-message");

// Muestra el resultado con texto e ícono (el estado no se comunica con color).
function showMessage(icon, text) {
  message.textContent = `${icon} ${text}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!form.checkValidity()) {
    showMessage("✕", "Revisa los datos: nombre, teléfono (mínimo 7 dígitos) y motivo son obligatorios.");
    return;
  }

  const data = Object.fromEntries(new FormData(form));
  const button = form.querySelector("button");
  button.disabled = true;
  showMessage("…", "Enviando tu solicitud.");

  try {
    const response = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error("Respuesta no válida");

    form.reset();
    showMessage("✓", "Recibimos tu solicitud. Te contactaremos pronto.");
  } catch {
    showMessage("✕", "No pudimos enviar tu solicitud. Intenta de nuevo en unos minutos.");
  } finally {
    button.disabled = false;
  }
});

// El pie muestra la versión que reporta /health (por defecto dice v1).
fetch("/health")
  .then((response) => response.json())
  .then((health) => {
    document.getElementById("version").textContent = `Versión ${health.version}`;
  })
  .catch(() => {});
