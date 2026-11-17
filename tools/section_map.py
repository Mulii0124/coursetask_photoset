"""Report the absolute vertical offset of each major section on a page.

Renders the page inside a fixed-width iframe (Edge headless clamps its own window
to ~504px, so an iframe is the only way to get a true wide layout) and asks the
inner document where its sections sit.

    python _tools\section_map.py index.html 1440
"""
import json
import os
import re
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SITE = r"D:\minimax_work\site"
OUT = r"D:\minimax_work\_tools\shots"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
PROBE = os.path.join(SITE, "_qa-map.html")
REPORT = os.path.join(OUT, "_qa-map.json")
PORT = 8124

PAGE = sys.argv[1] if len(sys.argv) > 1 else "index.html"
W = int(sys.argv[2]) if len(sys.argv) > 2 else 1440

PROBE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>map</title>
<style>html,body{margin:0;padding:0;overflow:hidden}iframe{width:%dpx;height:1000px;border:0;display:block}</style>
</head><body><iframe id="f"></iframe>
<script>
var q = new URLSearchParams(location.search);
var f = document.getElementById('f');
f.addEventListener('load', function () {
  var d = f.contentDocument, w = f.contentWindow;
  setTimeout(function () {
    var rows = [];
    Array.prototype.slice.call(d.querySelectorAll('section, .foot, .nav')).forEach(function (el) {
      var r = el.getBoundingClientRect();
      var top = r.top + w.scrollY;
      var label = (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
      var head = el.querySelector('h1, h2, .eyebrow');
      rows.push({ sel: el.tagName.toLowerCase() + label, top: Math.round(top), h: Math.round(r.height),
                  head: head ? (head.textContent || '').trim().slice(0, 28) : '' });
    });
    fetch('/report', { method: 'POST', body: JSON.stringify({
      page: q.get('p'), scrollHeight: d.documentElement.scrollHeight, rows: rows }) });
  }, 1500);
});
f.src = q.get('p');
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        with open(REPORT, "wb") as f:
            f.write(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(PROBE, "w", encoding="utf-8", newline="\n") as f:
        f.write(PROBE_HTML % W)

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    if os.path.exists(REPORT):
        os.remove(REPORT)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + PROFILE,
           "--virtual-time-budget=9000",
           "--window-size=%d,1100" % (W + 20),
           "http://127.0.0.1:%d/_qa-map.html?p=%s" % (PORT, PAGE)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if not os.path.exists(REPORT):
        print("NO REPORT")
        srv.shutdown()
        return
    with open(REPORT, "r", encoding="utf-8") as f:
        r = json.load(f)
    print("%s  scrollHeight=%d" % (r["page"], r["scrollHeight"]))
    for row in r["rows"]:
        print("  top=%-6d h=%-6d %-42s %s" % (row["top"], row["h"], row["sel"][:42], row["head"]))

    srv.shutdown()
    if os.path.exists(PROBE):
        os.remove(PROBE)


if __name__ == "__main__":
    main()
