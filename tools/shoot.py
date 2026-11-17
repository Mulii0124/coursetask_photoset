"""Desktop-width headless captures (Edge) for visual QA of the wide layout."""
import os
import subprocess
import sys

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = r"D:\minimax_work\_tools\shots"
PROFILE = os.path.join(os.environ["TEMP"], "edge-qa-profile")
os.makedirs(OUT, exist_ok=True)

SHOTS = [
    ("index-hero",     "http://127.0.0.1:8099/index.html",           1440, 900),
    ("index-catalogue","http://127.0.0.1:8099/index.html#catalogue", 1440, 2200),
    ("index-story",    "http://127.0.0.1:8099/index.html",           1440, 6000),
    ("works",          "http://127.0.0.1:8099/works.html",           1440, 2000),
    ("series-begin",   "http://127.0.0.1:8099/series-begin.html",   1440, 2400),
    ("series-days",    "http://127.0.0.1:8099/series-days.html",    1440, 2400),
    ("series-journey", "http://127.0.0.1:8099/series-journey.html", 1440, 2400),
    ("series-temple",  "http://127.0.0.1:8099/series-temple.html",  1440, 2400),
    ("journal",        "http://127.0.0.1:8099/journal.html",         1440, 1600),
    ("about",          "http://127.0.0.1:8099/about.html",           1440, 1800),
    ("contact",        "http://127.0.0.1:8099/contact.html",         1440, 1200),
]

only = sys.argv[1:] if len(sys.argv) > 1 else None

for name, url, w, h in SHOTS:
    if only and name not in only:
        continue
    png = os.path.join(OUT, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    cmd = [
        EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        "--user-data-dir=" + PROFILE,
        "--virtual-time-budget=9000",
        "--window-size=%d,%d" % (w, h),
        "--screenshot=" + png,
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    ok = os.path.exists(png)
    print("%-18s %s  %s" % (name, "OK " if ok else "FAIL", (str(os.path.getsize(png) // 1024) + " KB") if ok else r.stderr[-200:]))
