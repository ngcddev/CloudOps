# Tope del tamaño del cuerpo de una petición (auditoría BE-05): el Ingress entra directo al Pod, que tiene 256 Mi, y sin tope un cuerpo enorme se
# leía entero en memoria. Responde 413 antes de leer nada si el `Content-Length` ya lo declara demasiado grande, y corta durante la lectura si
# el cuerpo llega por trozos sin declarar su tamaño.
import json

from starlette.exceptions import HTTPException


def _message(limite: int) -> str:
    return f"La petición es demasiado grande: el máximo es {limite // 1024} KB."


class BodySizeLimit:
    """Middleware ASGI. `rutas` da el tope de las rutas que empiezan por cada prefijo; el resto usa `por_defecto`."""

    def __init__(self, app, por_defecto: int, rutas: dict[str, int] | None = None):
        self.app = app
        self.por_defecto = por_defecto
        self.rutas = rutas or {}

    def _limit(self, ruta: str) -> int:
        for prefijo, limite in self.rutas.items():
            if ruta.startswith(prefijo):
                return limite
        return self.por_defecto

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return
        limite = self._limit(scope["path"])
        declarado = dict(scope["headers"]).get(b"content-length")
        if declarado is not None and declarado.isdigit() and int(declarado) > limite:
            cuerpo = json.dumps({"detail": _message(limite)}, ensure_ascii=False).encode()
            await send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(cuerpo)).encode())]})
            await send({"type": "http.response.body", "body": cuerpo})
            return

        recibidos = 0

        async def limited_receive():
            """Lee el cuerpo por partes y corta con 413 en cuanto supera el límite."""
            nonlocal recibidos
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                recibidos += len(mensaje.get("body", b""))
                if recibidos > limite:
                    # Una HTTPException: FastAPI la deja pasar tal cual (a otras las vuelve «error al leer el cuerpo», 400) y responde 413
                    raise HTTPException(status_code=413, detail=_message(limite))
            return mensaje

        await self.app(scope, limited_receive, send)
