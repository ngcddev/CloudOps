# Gitea falso para las pruebas (spec 005): un servidor HTTP local que implementa solo la parte de la
# API de contenidos que usa el Hub (GET y PUT /repos/{repo}/contents/{path}) y guarda cada commit.
import base64
import hashlib
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def _blob_sha(text: str) -> str:
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class FakeGitea:
    def __init__(self, files: dict[str, str], repo: str = "forja-digital/hub-gitops", token: str = "token-de-prueba"):
        self.files = dict(files)
        self.repo = repo
        self.token = token
        self.commits: list[dict] = []
        self.requests: list[tuple[str, str]] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silencio en la salida de pytest
                pass

            def _send(self, status: int, body: dict):
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _route(self):
                fake.requests.append((self.command, self.path))
                if self.headers.get("Authorization") != f"token {fake.token}":
                    self._send(401, {"message": "token is required"})
                    return None
                match = re.fullmatch(rf"/api/v1/repos/{re.escape(fake.repo)}/contents/([^?]+)(\?.*)?", self.path)
                if not match:
                    self._send(404, {"message": "not found"})
                    return None
                return match.group(1)

            def do_GET(self):
                path = self._route()
                if path is None:
                    return
                if path not in fake.files:
                    return self._send(404, {"message": "file not found"})
                text = fake.files[path]
                self._send(200, {
                    "path": path,
                    "sha": _blob_sha(text),
                    "content": base64.b64encode(text.encode()).decode(),
                })

            def do_PUT(self):
                path = self._route()
                if path is None:
                    return
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if path not in fake.files:
                    return self._send(404, {"message": "file not found"})
                if body.get("sha") != _blob_sha(fake.files[path]):
                    return self._send(409, {"message": "sha does not match"})
                fake.files[path] = base64.b64decode(body["content"]).decode()
                sha = hashlib.sha1(f"{len(fake.commits)}{body['message']}".encode()).hexdigest()
                fake.commits.append({
                    "sha": sha,
                    "message": body["message"],
                    "author": body["author"],
                    "path": path,
                })
                self._send(200, {"commit": {"sha": sha, "message": body["message"]}, "content": {"path": path}})

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "FakeGitea":
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._server.shutdown()
        self._server.server_close()
