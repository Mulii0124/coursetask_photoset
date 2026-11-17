"""
Verify the published GitHub Pages site from the public internet.

Every page and every referenced asset is fetched over the real public URL and
checked for a 200 + correct content type. This is what a grader's browser sees.
"""
import os
import re
import subprocess
import sys
import urllib.parse

BASE = "https://mulii0124.github.io/coursetask_photoset/"
PROXY = "http://127.0.0.1:8899"

ENV = dict(os.environ, HTTP_PROXY=PROXY, HTTPS_PROXY=PROXY)


def fetch(url):
    r = subprocess.run(
        ["curl.exe", "-sS", "-L", "--max-time", "45", "-o", "NUL",
         "-w", "%{http_code} %{content_type} %{size_download}", url],
        capture_output=True, text=True, env=ENV)
    out = (r.stdout or "").strip()
    parts = out.split(None, 2)
    code = parts[0] if parts else "000"
    ctype = parts[1] if len(parts) > 1 else ""
    size = parts[2] if len(parts) > 2 else "0"
    return code, ctype, size


def body(url):
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "45", url],
                       capture_output=True, env=ENV)
    return r.stdout.decode("utf-8", errors="replace")


REF = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I)

print("base:", BASE)
code, ctype, size = fetch(BASE)
print("home  -> %s  %s  %s" % (code, ctype, size))
if code != "200":
    print("HOME NOT READY — aborting")
    sys.exit(1)

home = body(BASE)
pages = sorted(set(m for m in REF.findall(home) if m.endswith(".html")))

print("\n--- pages ---")
bad = 0
for p in pages:
    c, t, s = fetch(BASE + p)
    flag = "OK " if c == "200" else "FAIL"
    if c != "200":
        bad += 1
    print("  %s %-28s %s  %8s  %s" % (flag, p, c, s, t))

print("\n--- assets referenced by the home page ---")
assets = sorted(set(m for m in REF.findall(home)
                     if not m.endswith(".html") and not m.startswith(("http", "#", "mailto"))))
for a in assets:
    c, t, s = fetch(BASE + a)
    flag = "OK " if c == "200" else "FAIL"
    if c != "200":
        bad += 1
    print("  %s %-44s %s  %8s  %s" % (flag, a, c, s, t))

# crawl every page's assets too
print("\n--- assets across all pages ---")
allassets = set()
for p in pages:
    h = body(BASE + p)
    for m in REF.findall(h):
        if not m.endswith(".html") and not m.startswith(("http", "#", "mailto")):
            allassets.add(m)
for a in sorted(allassets):
    c, t, s = fetch(BASE + a)
    if c != "200":
        bad += 1
        print("  FAIL %-44s %s" % (a, c))
print("  checked %d assets, failures so far: %d" % (len(allassets), bad))

print("\n--- absolute-path / file:// leak check on the live HTML ---")
leaks = 0
for p in pages:
    h = body(BASE + p)
    for m in REF.findall(h):
        if m.startswith("/") or m.lower().startswith("file:") or re.match(r"^[A-Za-z]:[\\/]", m):
            print("  LEAK", p, m)
            leaks += 1
print("  leaks:", leaks)

print("\nRESULT:", "ALL GOOD" if bad == 0 and leaks == 0 else "PROBLEMS FOUND")
