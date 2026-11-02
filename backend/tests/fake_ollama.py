# Asistente simulado para las pruebas (spec 012): responde como lo haría Ollama, sin red ni GPU.
# Tiene la misma interfaz que tendrá integrations/ollama.py (T17): write(kind, facts) -> WriterResult.
from app.services.ai_drafts import WriterError, WriterResult


class FakeOllama:
    """Redacta con los hechos que recibe; se le puede pedir que falle o que devuelva un texto fijo por tipo."""

    model = "fake-qwen2.5:7b"
    prompt_version = "v1"

    def __init__(self, texts: dict[str, str] | None = None, fail: bool = False):
        self.texts = texts or {}
        self.fail = fail
        # Lo que el Hub le pidió, para comprobar que solo recibió hechos del Hub
        self.calls: list[tuple[str, dict]] = []

    def write(self, kind: str, facts: dict) -> WriterResult:
        self.calls.append((kind, facts))
        if self.fail:
            raise WriterError("El asistente no respondió en 60 segundos.")
        text = self.texts.get(kind) or self._default(kind, facts)
        return WriterResult(text=text, model=self.model, prompt_version=self.prompt_version)

    @staticmethod
    def _default(kind: str, facts: dict) -> str:
        if kind == "resumen":
            return (
                f"Incidente {facts['priority']} en {facts['service']}: empezó a las {facts['start_time']} y se "
                f"recuperó a las {facts['end_time']} con rollback de {facts['from_version']} a "
                f"{facts['to_version']}. Duración: {facts['duration_minutes']} minutos."
            )
        return (
            f"Detectamos una falla temporal en su sitio a las {facts['start_time']}. Activamos la recuperación "
            f"y a las {facts['end_time']} el servicio volvió a funcionar."
        )
