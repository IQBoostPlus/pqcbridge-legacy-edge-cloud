"""Minimal HTTP health endpoint (project prompt section 8).

A deliberately tiny http.server-based health check. Not a monitoring
system.

TODO: Student review required.
  - Consider what else a health check should report (dependency
    status, degraded states) and how it should be secured.
  - The endpoint binds 0.0.0.0 and is unauthenticated.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def make_health_server(port: int, service: str, status_provider,
                       extra_routes: dict = None) -> threading.Thread:
    """Start a /health HTTP endpoint on a background thread.

    status_provider() must return a dict merged into the JSON response.
    extra_routes maps additional GET paths to callables returning
    JSON-serializable data (e.g. the cloud's /readings demo endpoint).
    """
    provider = status_provider
    routes = dict(extra_routes or {})

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - http.server naming convention
            if self.path in routes:
                try:
                    payload = json.dumps(routes[self.path]()).encode("utf-8")
                    self._respond(payload)
                except Exception as exc:  # noqa: BLE001 - health must not crash
                    self.send_error(500, type(exc).__name__)
                return
            if self.path != "/health":
                self.send_error(404)
                return
            body = {"status": "ok", "service": service}
            try:
                body.update(provider())
            except Exception as exc:  # noqa: BLE001 - health must not crash
                body = {"status": "degraded", "service": service,
                        "error": type(exc).__name__}
            self._respond(json.dumps(body).encode("utf-8"))

        def _respond(self, payload: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):  # keep health logs quiet
            pass

    def _serve():
        server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        server.serve_forever()

    thread = threading.Thread(target=_serve, name=f"health-{service}",
                              daemon=True)
    thread.start()
    return thread
