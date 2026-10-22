# Argo CD falso para las pruebas (spec 005): servidor HTTP local con GET /api/v1/applications/{name}.
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class FakeArgoCD:
    def __init__(self, apps: dict[str, dict], token: str = "token-de-prueba"):
        # apps: nombre -> {"sync": "Synced", "health": "Healthy", "revision": "<sha>"}
        self.apps = dict(apps)
        self.token = token
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, status: int, body: dict):
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.headers.get("Authorization") != f"Bearer {fake.token}":
                    return self._send(401, {"error": "no autenticado"})
                prefix = "/api/v1/applications/"
                name = self.path[len(prefix):] if self.path.startswith(prefix) else None
                app = fake.apps.get(name)
                if app is None:
                    return self._send(404, {"error": "application not found"})
                self._send(200, {
                    "metadata": {"name": name},
                    "status": {
                        "sync": {"status": app["sync"], "revision": app.get("revision")},
                        "health": {"status": app["health"]},
                    },
                })

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "FakeArgoCD":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._server.shutdown()
        self._server.server_close()
