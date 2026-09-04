#!/usr/bin/env python3
"""nomi - minimal disposable chatbot. stdlib only, no deps.

Run:
  cp .env.example .env   # edit CODEX_URL
  python3 server.py
  # open http://localhost:3000
  # ngrok: ngrok http 3000

What it does:
  GET  /         -> serves index.html
  POST /api/chat {prompt} -> forwards to $CODEX_URL/exec with hardcoded
                             body, returns {output} to the browser.
"""
import json
import os
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ---- .env loader (no dependency) ----
def load_dotenv(path=BASE_DIR / ".env"):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'").strip('"')
        os.environ.setdefault(k, v)

load_dotenv()

# ---- config: URL comes from .env, rest is hardcoded ----
CODEX_URL = os.environ.get("CODEX_URL", "").rstrip("/")
PORT = int(os.environ.get("PORT", "3000"))

# Hidden prefix prepended to every prompt. Never shown in the UI.
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "").strip()

MODEL = "gpt-5.6-luna"
EFFORT = "medium"
SANDBOX = "workspace-write"
WORKDIR = os.environ.get("WORKDIR", "/tmp/my-project")
TIMEOUT_MS = 300000
JSON_MODE = False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet; change to super().log_message() for logs

    def _send(self, code, body: bytes, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = (BASE_DIR / "index.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, b'{"ok":true}', "application/json")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/chat":
            return self._send(404, b'{"error":"not found"}')
        if not CODEX_URL:
            return self._send(
                500,
                json.dumps({"error": "CODEX_URL not set. Put it in .env"}).encode(),
            )
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send(400, b'{"error":"invalid json"}')

        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return self._send(400, b'{"error":"empty prompt"}')

        # hardcoded body — frontend only sends `prompt`
        # (no `approval`: exec is non-interactive, always never server-side)
        # SYSTEM_PROMPT (from .env) is prepended invisibly, never shown in the UI
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}" if SYSTEM_PROMPT else prompt
        payload = {
            "prompt": full_prompt,
            "workdir": WORKDIR,
            "model": MODEL,
            "effort": EFFORT,
            "sandbox": SANDBOX,
            "timeoutMs": TIMEOUT_MS,
            "json": JSON_MODE,
        }

        print(f"-> exec ({len(prompt)} chars): {prompt[:80]!r}")
        if SYSTEM_PROMPT:
            print(f"   (+ hidden system prompt, {len(SYSTEM_PROMPT)} chars)")
        req = urllib.request.Request(
            CODEX_URL + "/exec",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            # +10s buffer over the codex timeout
            with urllib.request.urlopen(req, timeout=TIMEOUT_MS / 1000 + 10) as r:
                upstream = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"<- upstream {e.code}")
            return self._send(
                502,
                json.dumps({"error": f"upstream {e.code}: {body[:500]}"}).encode(),
            )
        except Exception as e:
            print(f"<- failed: {e}")
            return self._send(
                502, json.dumps({"error": f"upstream failed: {e}"}).encode()
            )

        # only `output` is shown on screen; fall back to stderr/raw so
        # "(empty)" never hides what the backend actually returned
        output = (upstream.get("output") or "").strip()
        if not output:
            output = (
                (upstream.get("stderr") or "").strip()
                or (upstream.get("error") or "")
                or json.dumps(upstream)[:3000]
            )
        print(f"<- ok ({len(output)} chars)")
        self._send(200, json.dumps({"output": output}).encode())


if __name__ == "__main__":
    print(f"nomi on http://localhost:{PORT}  ->  {CODEX_URL or '(CODEX_URL missing)'}/exec")
    try:
        ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nnomi stopped. bye!")
