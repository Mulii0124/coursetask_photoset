"""True narrow-viewport captures.

Edge headless clamps its window to a ~504px minimum width, so `--window-size=390`
renders a 504px layout and then crops the PNG to 390 — a false "overflow".
This shoots each page inside a fixed-width iframe instead, which gives a real
390px layout viewport.
"""
import os
import subprocess

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SITE = r"D:\minimax_work\site"
OUT = r"D:\minimax_work\_tools\shots"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
TMP = os.path.join(SITE, "_qa-frame.html")
os.makedirs(OUT, exist_ok=True)

W, H = 390, 844

SHOTS = [
    ("m-index",    "index.html",          0),
    ("m-catalogue", "index.html",         900),   # scroll offset inside the frame
    ("m-works",    "works.html",          0),
    ("m-series",   "series-temple.html", 0),
    ("m-journal",  "journal.html",        0),
    ("m-about",    "about.html",          0),
    ("m-contact",  "contact.html",        0),
]

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;background:#0a0a0b;overflow:hidden}}
iframe{{width:{w}px;height:{h}px;border:0;display:block}}</style></head>
<body><iframe id="f" src="{src}"></iframe>
<script>
document.getElementById('f').addEventListener('load', function () {{
  if ({scroll}) {{ document.getElementById('f').contentWindow.scrollTo(0, {scroll}); }}
}});
</script></body></html>"""

for n, (name, page, scroll) in enumerate(SHOTS):
    # unique cache-buster per shot: Edge would otherwise reuse the cached
    # outer document and keep showing the previously captured page
    with open(TMP, "w", encoding="utf-8", newline="\n") as f:
        f.write(TPL.format(w=W, h=H, src=page + "?v=%d" % n, scroll=scroll))
    png = os.path.join(OUT, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + PROFILE,
           "--virtual-time-budget=9000",
           "--window-size=%d,%d" % (W + 20, H + 20),
           "--screenshot=" + png,
           "http://127.0.0.1:8099/_qa-frame.html?v=%d" % n]
    subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    print("%-12s %s" % (name, ("OK  %d KB" % (os.path.getsize(png) // 1024)) if os.path.exists(png) else "FAIL"))

if os.path.exists(TMP):
    os.remove(TMP)
