#!/usr/bin/env python3
"""
Fantasy Draft War Room - local server
Serves the app and proxies requests to ESPN, Sleeper, and the Anthropic API
(browsers block these calls directly due to CORS; this tiny server fixes that).

Run:  python3 server.py
Then open:  http://localhost:8432
"""
import json
import os
import ssl
import urllib.request
import urllib.error
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8432
ROOT = os.path.dirname(os.path.abspath(__file__))


def make_ssl_context():
    """macOS Pythons often can't find the system cert store; find one that works."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for cafile in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


SSL_CTX = make_ssl_context()

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

_sleeper_cache = {"data": None}


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
        return r.read()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("  " + fmt % args)

    def respond(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self.respond(400, b'{"error":"bad json"}')
            return
        try:
            if self.path == "/api/espn":
                self.handle_espn(body)
            elif self.path == "/api/sleeper":
                self.handle_sleeper()
            elif self.path == "/api/claude":
                self.handle_claude(body)
            else:
                self.respond(404, b'{"error":"not found"}')
        except urllib.error.HTTPError as e:
            detail = e.read()[:2000].decode("utf-8", "replace")
            msg = json.dumps({"error": f"Upstream HTTP {e.code}", "detail": detail})
            self.respond(502, msg.encode())
        except Exception as e:
            self.respond(500, json.dumps({"error": str(e)}).encode())

    # ---- ESPN fantasy API (private leagues need SWID + espn_s2 cookies) ----
    def handle_espn(self, body):
        league = urllib.parse.quote(str(body["leagueId"]))
        season = int(body.get("season", 2026))
        views = body.get("views", [])
        url = (f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
               f"seasons/{season}/segments/0/leagues/{league}")
        if views:
            url += "?" + "&".join("view=" + urllib.parse.quote(v) for v in views)
        headers = {"Accept": "application/json"}
        swid, s2 = body.get("swid", "").strip(), body.get("s2", "").strip()
        if swid and s2:
            if not swid.startswith("{"):
                swid = "{" + swid.strip("{}") + "}"
            headers["Cookie"] = f"SWID={swid}; espn_s2={s2}"
        if body.get("filter"):
            headers["X-Fantasy-Filter"] = json.dumps(body["filter"])
        self.respond(200, http_get(url, headers))

    # ---- Sleeper players (public API, ~10 MB, cached in memory) ----
    def handle_sleeper(self):
        if _sleeper_cache["data"] is None:
            _sleeper_cache["data"] = http_get("https://api.sleeper.app/v1/players/nfl")
        self.respond(200, _sleeper_cache["data"])

    # ---- Anthropic API ----
    def handle_claude(self, body):
        key = body.get("apiKey", "").strip()
        if not key:
            self.respond(400, b'{"error":"No API key set. Add it on the Setup tab."}')
            return
        payload = json.dumps(body["payload"]).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload, method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            })
        with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
            self.respond(200, r.read())


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=ROOT))
    print(f"\n  Fantasy Draft War Room running at  http://localhost:{PORT}\n"
          f"  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
