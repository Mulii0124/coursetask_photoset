"""Capture below-the-fold sections at desktop width.

Edge headless cannot scroll a page before screenshotting, so each target page is
rendered inside a fixed-width iframe whose inner document is scrolled by script.
"""
import os
import subprocess

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SITE = r"D:\minimax_work\site"
OUT = r"D:\minimax_work\_tools\shots"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
TMP = os.path.join(SITE, "_qa-scroll.html")
os.makedirs(OUT, exist_ok=True)

W, H = 1440, 2200

SHOTS = [
    ("index-catalogue", "index.html", 950),
    ("index-interlude", "index.html", 2200),
    ("index-story",     "index.html", 3240),
    ("index-profile",   "index.html", 4250),
    ("index-foot",      "index.html", 4400),
    ("begin-split",     "series-begin.html", 5000),
    ("begin-samples",   "series-begin.html", 6200),
]

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:#0a0a0b;overflow:hidden}}
iframe{{width:{w}px;height:{h}px;border:0;display:block}}</style></head>
<body><iframe id="f" src="{src}"></iframe>
<script>
document.getElementById('f').addEventListener('load', function () {{
  var w = this.contentWindow;
  w.document.documentElement.style.scrollBehavior = 'auto';
  w.document.body.style.scrollBehavior = 'auto';
  try {{ w.scrollTo({{ top: {scroll}, left: 0, behavior: 'instant' }}); }} catch (e) {{ w.scrollTo(0, {scroll}); }}
}});
</script></body></html>"""

for n, (name, page, scroll) in enumerate(SHOTS):
    with open(TMP, "w", encoding="utf-8", newline="\n") as f:
        f.write(TPL.format(w=W, h=H, src=page + "?v=s%d" % n, scroll=scroll))
    png = os.path.join(OUT, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + PROFILE,
           "--virtual-time-budget=12000",
           "--window-size=%d,%d" % (W + 20, H + 20),
           "--screenshot=" + png,
           "http://127.0.0.1:8099/_qa-scroll.html?v=%d" % n]
    subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    print("%-16s %s" % (name, ("OK  %d KB" % (os.path.getsize(png) // 1024)) if os.path.exists(png) else "FAIL"))

if os.path.exists(TMP):
    os.remove(TMP)
