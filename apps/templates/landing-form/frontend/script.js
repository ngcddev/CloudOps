const form = document.getElementById('contact-form');
const statusMessage = document.getElementById('status-message');

const setStatus = (message, type) => {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = {
    name: document.getElementById('name').value.trim(),
    phone: document.getElementById('phone').value.trim(),
    reason: document.getElementById('reason').value.trim(),
  };

  setStatus('Enviando solicitud...', '');

  try {
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok || !data.ok) {
      throw new Error('La solicitud no fue aceptada.');
    }

    form.reset();
    setStatus('Tu consulta fue enviada correctamente. Pronto te contactaremos.', 'success');
  } catch (error) {
    setStatus('No pudimos enviar tu información. Inténtalo de nuevo.', 'error');
  }
});
