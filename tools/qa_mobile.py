"""Automated narrow-viewport QA.

Edge headless clamps its window to a ~504px minimum, so a true 390px layout can
only be obtained by rendering the page inside a fixed-width iframe. This script
serves the site over HTTP with a POST sink, drives Edge headless at that iframe
size, and collects the measurements each page reports back.

Reports for every page:
  * horizontal overflow (document scroll width vs viewport width)
  * elements whose box extends past the right edge
  * elements whose box extends past the left edge
  * images that failed to decode (broken images)
"""
import json
import os
import re
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
REPORT = os.path.join(OUT, "_qa-report.json")
PORT = 8123
W, H = 390, 844
if len(sys.argv) > 1:
    W = int(sys.argv[1])
if len(sys.argv) > 2:
    H = int(sys.argv[2])
TAG = "qa-mobile" if W < 800 else "qa-desktop"

PAGES = sorted(f for f in os.listdir(SITE) if f.endswith(".html") and not f.startswith("_"))

PROBE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>qa</title>
<style>html,body{margin:0;padding:0;overflow:hidden}iframe{width:%dpx;height:%dpx;border:0;display:block}</style>
</head><body><iframe id="f"></iframe>
<script>
var q = new URLSearchParams(location.search);
var f = document.getElementById('f');
f.addEventListener('load', function () {
  var d = f.contentDocument, w = f.contentWindow;
  setTimeout(function () {
    var vw = w.innerWidth;
    var bad = [], broken = [], wide = [];
    Array.prototype.slice.call(d.querySelectorAll('body *')).forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (!r.width && !r.height) return;
      var tag = el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : '');
      if (r.right > vw + 1) bad.push({ el: tag, right: Math.round(r.right), left: Math.round(r.left), w: Math.round(r.width) });
      if (r.left < -1) bad.push({ el: tag, left: Math.round(r.left), right: Math.round(r.right) });
    });
    Array.prototype.slice.call(d.images).forEach(function (im) {
      if (!im.complete || im.naturalWidth === 0) broken.push(im.getAttribute('src'));
    });
    var out = {
      page: q.get('p'),
      innerWidth: vw,
      docScrollWidth: d.documentElement.scrollWidth,
      bodyScrollWidth: d.body.scrollWidth,
      scrollHeight: d.documentElement.scrollHeight,
      images: d.images.length,
      brokenImages: broken,
      overflow: bad.slice(0, 15),
      overflowCount: bad.length
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
    # a warm profile can serve a stale stylesheet and make the overflow
    # numbers describe the wrong layout — start clean
    shutil.rmtree(PROFILE, ignore_errors=True)
    with open(PROBE, "w", encoding="utf-8", newline="\n") as f:
        f.write(PROBE_HTML % (W, H))

    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    results = []
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
            results.append({"page": page, "error": "no report"})
            continue
        with open(REPORT, "r", encoding="utf-8") as f:
            r = json.load(f)
        results.append(r)
        flag = "OK  " if (r["overflowCount"] == 0 and not r["brokenImages"]
                          and r["docScrollWidth"] <= r["innerWidth"] + 1) else "FAIL"
        print("%s %-22s vw=%d doc=%d imgs=%d broken=%d overflow=%d" % (
            flag, page, r["innerWidth"], r["docScrollWidth"], r["images"],
            len(r["brokenImages"]), r["overflowCount"]))
        for b in r["overflow"][:6]:
            print("      overflow: %s" % json.dumps(b, ensure_ascii=False))
        for b in r["brokenImages"][:6]:
            print("      broken:   %s" % b)

    srv.shutdown()
    if os.path.exists(PROBE):
        os.remove(PROBE)
    with open(os.path.join(OUT, TAG + ".json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    bad = [r for r in results
           if r.get("error") or r["overflowCount"] or r["brokenImages"]
           or r["docScrollWidth"] > r["innerWidth"] + 1]
    print("\n" + "=" * 60)
    print("RESULT:", "ALL PAGES CLEAN AT %dpx" % W if not bad else "PROBLEMS: %s" % [b["page"] for b in bad])


if __name__ == "__main__":
    main()
