"""Final acceptance check against the live GitHub Pages site."""
import os
import re
import subprocess
import sys
import time

BASE = "https://mulii0124.github.io/coursetask_photoset/"
PROXY = "http://127.0.0.1:8899"
ENV = dict(os.environ, HTTP_PROXY=PROXY, HTTPS_PROXY=PROXY)
fails = []


def raw(url):
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", url],
                       capture_output=True, env=ENV)
    return r.stdout


def head(url):
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", "-o", "NUL",
                        "-w", "%{http_code} %{content_type} %{size_download}", url],
                       capture_output=True, text=True, env=ENV)
    return (r.stdout or "").strip()


# ---- wait for the rebuild to pick up the new commit -----------------------
print("waiting for Pages to serve the latest commit...")
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "assets", "js", "site.js")
LOCAL = os.path.normpath(LOCAL)
want = os.path.getsize(LOCAL)
for i in range(40):
    h = raw(BASE + "assets/js/site.js")
    if len(h) == want:
        print("  latest commit is live (%d bytes of site.js)\n" % want)
        break
    time.sleep(15)
else:
    print("  TIMEOUT waiting for the rebuild")

PAGES = ["index.html", "works.html", "series-garden.html", "series-lantern.html",
         "series-sky.html", "series-street.html", "series-journey.html",
         "journal.html", "about.html", "contact.html"]

print("--- 1. pages ---")
for p in PAGES:
    c = head(BASE + p)
    ok = c.startswith("200")
    if not ok:
        fails.append("page %s -> %s" % (p, c))
    print("  %s %-24s %s" % ("OK " if ok else "FAIL", p, c))

print("\n--- 2. assets (every reference on every page) ---")
assets = set()
for p in PAGES:
    html = raw(BASE + p).decode("utf-8", errors="replace")
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html):
        if not m.group(1).endswith(".html"):
            assets.add(m.group(1))
bad = 0
for a in sorted(assets):
    c = head(BASE + a)
    if not c.startswith("200"):
        fails.append("asset %s -> %s" % (a, c))
        bad += 1
print("  %d assets, %d failures" % (len(assets), bad))

print("\n--- 3. no absolute paths / file:// / drive letters / absolute URLs ---")
leaks = 0
for p in PAGES:
    html = raw(BASE + p).decode("utf-8", errors="replace")
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html):
        v = m.group(1)
        if (v.startswith("/") or v.lower().startswith("file:") or re.match(r"^[A-Za-z]:[\\/]", v)
                or re.match(r"^(?:https?:|mailto:|tel:|ftp:|//)", v, re.I)):
            print("  LEAK %s -> %s" % (p, v))
            leaks += 1
            fails.append("leak %s %s" % (p, v))
print("  leaks:", leaks)

print("\n--- 4. line endings (LF only, no CRLF) ---")
for p in ["index.html", "assets/css/site.css", "assets/js/site.js"]:
    b = raw(BASE + p)
    crlf = b.count(b"\r\n")
    print("  %-24s CRLF=%d bytes=%d" % (p, crlf, len(b)))
    if crlf:
        fails.append("%s has CRLF" % p)

print("\n--- 5. index links to every other page ---")
idx = raw(BASE + "index.html").decode("utf-8", errors="replace")
for p in PAGES:
    if p == "index.html":
        continue
    if ('href="%s"' % p) in idx:
        print("  OK  index.html -> %s" % p)
    else:
        print("  FAIL index.html -> %s" % p)
        fails.append("index missing link to %s" % p)

print("\n--- 6. catalogue slot markup on the live page ---")
slot = re.search(r'<figure class="slot".*?</figure>', idx, re.S)
print("  " + (slot.group(0).replace("\n", " ") if slot else "NOT FOUND"))
if not slot or 'data-role="a"' not in slot.group(0) or 'data-role="b"' not in slot.group(0):
    fails.append("slot markup wrong")

print("\n--- 7. no external CDN dependency ---")
cdn = re.findall(r'https?://(?!mulii0124\.github\.io)[^"\'\s)]+', idx)
cdn = [c for c in cdn if "schema.org" not in c and "w3.org" not in c]
print("  external refs in index.html:", cdn if cdn else "none")

print("\n" + "=" * 60)
print("RESULT:", "ALL CHECKS PASSED" if not fails else "FAILURES: %s" % fails)
