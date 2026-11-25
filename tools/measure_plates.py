"""Measure the rendered size of every plate on every series page.

Same iframe trick as qa_mobile.py (Edge headless clamps its own window, so a
true viewport width is only reachable inside a fixed-width iframe). Reports the
box of each `.plate--full` and of the image inside it, so the "the photographs
are too big" complaint can be checked with numbers instead of by eye.

Usage: python measure_plates.py [width] [height]   (default 1440 x 900)
"""
import json
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SITE = r"D:\minimax_work\site"
OUT = r"D:\minimax_work\_tools\shots"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
PROBE = os.path.join(SITE, "_qa-probe.html")
REPORT = os.path.join(OUT, "_measure.json")
PORT = 8127
W, H = 1440, 900
if len(sys.argv) > 1:
    W = int(sys.argv[1])
if len(sys.argv) > 2:
    H = int(sys.argv[2])

PAGES = sorted(f for f in os.listdir(SITE)
                if f.startswith("series-") and f.endswith(".html"))

PROBE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>measure</title>
<style>html,body{margin:0;padding:0;overflow:hidden}iframe{width:%dpx;height:%dpx;border:0;display:block}</style>
</head><body><iframe id="f"></iframe>
<script>
var q = new URLSearchParams(location.search);
var f = document.getElementById('f');
f.addEventListener('load', function () {
  var d = f.contentDocument, w = f.contentWindow;
  setTimeout(function () {
    var vw = w.innerWidth, vh = w.innerHeight, plates = [];
    Array.prototype.slice.call(d.querySelectorAll('.plate--full')).forEach(function (p) {
      var pr = p.getBoundingClientRect();
      var im = p.querySelector('img');
      var ir = im ? im.getBoundingClientRect() : null;
      plates.push({
        cls: p.className.replace(/\\s+/g, ' ').trim(),
        boxW: Math.round(pr.width), boxH: Math.round(pr.height),
        imgW: ir ? Math.round(ir.width) : 0,
        imgH: ir ? Math.round(ir.height) : 0,
        overScreen: ir ? (ir.height > vh + 1) : false
      });
    });
    var slot = d.querySelector('.slot');
    var sr = slot ? slot.getBoundingClientRect() : null;
    var out = {
      page: q.get('p'), innerWidth: vw, innerHeight: vh,
      plates: plates,
      slot: sr ? { w: Math.round(sr.width), h: Math.round(sr.height) } : null
    };
    fetch('/report', { method: 'POST', body: JSON.stringify(out) });
  }, 1200);
});
f.src = q.get('p');
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        with open(REPORT, "wb") as f:
            f.write(body)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(PROBE, "w", encoding="utf-8", newline="\n") as f:
        f.write(PROBE_HTML % (W, H))

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    widest = 0
    tallest = 0
    for page in PAGES:
        if os.path.exists(REPORT):
            os.remove(REPORT)
        cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--no-first-run", "--no-default-browser-check",
               "--user-data-dir=" + PROFILE,
               "--virtual-time-budget=9000",
               "--window-size=%d,%d" % (W + 20, H + 20),
               "http://127.0.0.1:%d/_qa-probe.html?p=%s" % (PORT, page)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if not os.path.exists(REPORT):
            print("%-24s NO REPORT" % page)
            continue
        with open(REPORT, "r", encoding="utf-8") as f:
            r = json.load(f)
        print("\n%s   viewport %dx%d" % (r["page"], r["innerWidth"], r["innerHeight"]))
        for p in r["plates"]:
            ratio = p["cls"].split()[-1]
            print("   %-8s img %4dx%-4d  box %4dx%-4d %s" % (
                ratio, p["imgW"], p["imgH"], p["boxW"], p["boxH"],
                "OVER SCREEN" if p["overScreen"] else ""))
            widest = max(widest, p["imgW"])
            tallest = max(tallest, p["imgH"])

    srv.shutdown()
    if os.path.exists(PROBE):
        os.remove(PROBE)
    print("\n" + "=" * 60)
    print("widest image : %dpx" % widest)
    print("tallest image: %dpx  (viewport height %d)" % (tallest, H))


if __name__ == "__main__":
    main()
