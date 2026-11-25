"""Check whether every rendered image keeps its natural aspect ratio.

A CSS `width: 100%` on an <img> that also carries width/height attributes
leaves the height pinned to the attribute value, which stretches the picture.
This script compares the rendered box against the intrinsic size of the file
and prints the distortion factor for anything off by more than 1%.

Usage: python check_ratio.py [width] [height]
"""
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SITE = r"D:\minimax_work\site"
OUT = r"D:\minimax_work\_tools\shots"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
PROBE = os.path.join(SITE, "_qa-probe.html")
REPORT = os.path.join(OUT, "_ratio.json")
PORT = 8129
W, H = 1440, 900
if len(sys.argv) > 1:
    W = int(sys.argv[1])
if len(sys.argv) > 2:
    H = int(sys.argv[2])

PAGES = sorted(f for f in os.listdir(SITE)
                if f.endswith(".html") and not f.startswith("_"))

PROBE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>ratio</title>
<style>html,body{margin:0;padding:0;overflow:hidden}iframe{width:%dpx;height:%dpx;border:0;display:block}</style>
</head><body><iframe id="f"></iframe>
<script>
var q = new URLSearchParams(location.search);
var f = document.getElementById('f');
f.addEventListener('load', function () {
  var d = f.contentDocument;
  setTimeout(function () {
    var imgs = [];
    Array.prototype.slice.call(d.images).forEach(function (im) {
      var r = im.getBoundingClientRect();
      if (!r.width || !r.height || !im.naturalWidth) return;
      var natural = im.naturalWidth / im.naturalHeight;
      var rendered = r.width / r.height;
      var fit = d.defaultView.getComputedStyle(im).objectFit;
      imgs.push({
        src: im.getAttribute('src'),
        natW: im.naturalWidth, natH: im.naturalHeight,
        boxW: Math.round(r.width * 10) / 10, boxH: Math.round(r.height * 10) / 10,
        factor: Math.round((rendered / natural) * 1000) / 1000,
        fit: fit,
        cls: (im.parentElement && im.parentElement.className) || ''
      });
    });
    fetch('/report', { method: 'POST', body: JSON.stringify({page: q.get('p'), imgs: imgs}) });
  }, 1500);
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

    def end_headers(self):
        # never let the browser reuse a cached copy of the CSS: a stale
        # stylesheet would silently invalidate every measurement here
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, *a):
        pass


def main():
    os.makedirs(OUT, exist_ok=True)
    # a warm profile can hand back a stale stylesheet, which silently
    # invalidates every number measured here — start from a clean slate
    shutil.rmtree(PROFILE, ignore_errors=True)
    with open(PROBE, "w", encoding="utf-8", newline="\n") as f:
        f.write(PROBE_HTML % (W, H))

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    bad = 0
    total = 0
    cropped = []
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
            print("%-22s NO REPORT" % page)
            continue
        with open(REPORT, "r", encoding="utf-8") as f:
            r = json.load(f)
        for im in r["imgs"]:
            total += 1
            off = abs(im["factor"] - 1.0) > 0.01
            if not off:
                continue
            if im.get("fit") == "cover":
                # a fixed-ratio frame cropping a differently shaped source on
                # purpose — that is the editorial crop, not a distortion
                cropped.append((page, im))
            else:
                bad += 1
                print("STRETCH %-20s %-38s natural %dx%d  box %.0fx%.0f  factor %.3f  fit=%s"
                      % (page, im["src"], im["natW"], im["natH"],
                         im["boxW"], im["boxH"], im["factor"], im.get("fit")))
        print("%-22s %d images checked" % (page, len(r["imgs"])))

    srv.shutdown()
    if os.path.exists(PROBE):
        os.remove(PROBE)
    print("\n" + "=" * 60)
    print("%d/%d images STRETCHED at %dpx  (distortion)"
          % (bad, total, W))
    print("%d images cropped on purpose (object-fit: cover in a fixed frame)"
          % len(cropped))
    for page, im in cropped:
        print("   crop  %-20s %-38s factor %.3f" % (page, im["src"], im["factor"]))


if __name__ == "__main__":
    main()
