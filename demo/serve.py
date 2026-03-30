"""Simple HTTP server for the 3D visualization demo."""

import http.server
import os

PORT = 8080

os.chdir(os.path.dirname(os.path.abspath(__file__)))

handler = http.server.SimpleHTTPServer if hasattr(http.server, "SimpleHTTPServer") \
    else http.server.SimpleHTTPRequestHandler

print(f"\n  Strategic Canvas 3D Demo")
print(f"  http://localhost:{PORT}")
print(f"  Press Ctrl+C to stop\n")

httpd = http.server.HTTPServer(("", PORT), http.server.SimpleHTTPRequestHandler)
httpd.serve_forever()
