"""
Demo server — serves the 5-column Strategic Canvas UI.

Usage:
  python demo/serve.py          # http://localhost:8080
  python demo/serve.py 3000     # custom port

This serves web/ (the 5-column React app) as /static/,
and demo_graph.json is auto-loaded by the frontend.
For the full WebSocket-powered experience, use: python main.py
"""

import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

# Serve from project root so /static/ maps to web/
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DemoHandler(http.server.SimpleHTTPRequestHandler):
    """Route / to web/index.html, /static/* to web/*."""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/web/index.html"
        elif self.path.startswith("/static/"):
            self.path = "/web/" + self.path[len("/static/"):]
        return super().do_GET()

    def log_message(self, format, *args):
        # Quieter logging
        if args and "200" not in str(args[1] if len(args) > 1 else ""):
            super().log_message(format, *args)


print(f"\n  Strategic Canvas — 5-Column Demo")
print(f"  http://localhost:{PORT}")
print(f"  (Static demo — no WebSocket. For full experience: python main.py)")
print(f"  Press Ctrl+C to stop\n")

httpd = http.server.HTTPServer(("", PORT), DemoHandler)
httpd.serve_forever()
