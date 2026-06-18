#!/usr/bin/env python3
"""
CROWN & OAK - Lowsec Scout : OPTIONAL local http server.
The default workflow does not need this: lowsec_scout.py writes lowsec_scout.html
to disk each run (and can git-push it). Use this only if you want a live http URL
on your machine instead of opening the file. Loopback only; pure stdlib.

  GET  /         -> the dashboard page (rendered from the last payload)
  GET  /data     -> the last payload as JSON
  GET  /health   -> "ok"
  POST /webhook  -> receive a payload (lowsec_scout.py --webhook) and persist it

    .venv\\Scripts\\python.exe scout_server.py            # http://127.0.0.1:8787
    .venv\\Scripts\\python.exe lowsec_scout.py --webhook http://127.0.0.1:8787/webhook
"""
import argparse, json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from scout_page import render_page   # shared renderer (single source of truth)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STATE_PATH = "webhook_state.json"
TOKEN = None
MAX_BODY = 1_000_000   # 1 MB cap on POST bodies


def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_state(d):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f)
    os.replace(tmp, STATE_PATH)


class Handler(BaseHTTPRequestHandler):
    server_version = "LowsecScout/1.0"

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/" or path == "/index.html":
            self._send(200, render_page(load_state()))
        elif path == "/data":
            self._send(200, json.dumps(load_state() or {}), "application/json; charset=utf-8")
        elif path == "/health":
            self._send(200, "ok", "text/plain; charset=utf-8")
        elif path == "/favicon.ico":
            self._send(204, b"")
        else:
            self._send(404, "not found", "text/plain; charset=utf-8")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path != "/webhook":
            self._send(404, '{"ok":false,"error":"not found"}', "application/json")
            return
        if TOKEN and self.headers.get("X-Webhook-Token") != TOKEN:
            self._send(401, '{"ok":false,"error":"bad token"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(400, '{"ok":false,"error":"bad length"}', "application/json")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict) or "systems" not in payload:
                raise ValueError("payload must be an object with a 'systems' list")
            save_state(payload)
        except Exception as e:
            self._send(400, json.dumps({"ok": False, "error": str(e)}), "application/json")
            return
        n = len(payload.get("systems") or [])
        self._send(200, json.dumps({"ok": True, "stored": n}), "application/json")

    def log_message(self, fmt, *args):
        sys.stderr.write("  [%s] %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    global TOKEN, STATE_PATH
    ap = argparse.ArgumentParser(description="Optional local page server for Lowsec Scout.")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (loopback only by default)")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--state", default=STATE_PATH, help="payload store path")
    ap.add_argument("--token", default=os.environ.get("SCOUT_WEBHOOK_TOKEN"),
                    help="optional shared secret required on POST /webhook")
    a = ap.parse_args()
    TOKEN = a.token or None
    STATE_PATH = a.state
    httpd = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"  CROWN & OAK - Lowsec Scout page on http://{a.host}:{a.port}/")
    print(f"  Webhook: POST http://{a.host}:{a.port}/webhook" + ("  (token required)" if TOKEN else ""))
    print("  Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()
