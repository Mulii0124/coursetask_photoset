"""Final acceptance check against the live GitHub Pages site.

The page list is discovered from the local site directory, so the check always
describes what is actually published instead of a hard-coded list that can drift
out of date after a rebuild.

    python _tools/final_check.py
"""
import hashlib
import os
import re
import subprocess
import sys
import time

BASE = "https://mulii0124.github.io/coursetask_photoset/"
PROXY = "http://127.0.0.1:8899"
ENV = dict(os.environ, HTTP_PROXY=PROXY, HTTPS_PROXY=PROXY)
fails = []


def find_site():
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(4):
        for c in (d, os.path.join(d, "site")):
            if os.path.isfile(os.path.join(c, "assets", "css", "site.css")):
                return os.path.normpath(c)
        d = os.path.dirname(d)
    raise SystemExit("cannot locate the site root (assets/css/site.css)")


SITE = find_site()


def raw(url):
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", url],
                       capture_output=True, env=ENV)
    return r.stdout


def head(url):
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", "-o", "NUL",
                        "-w", "%{http_code} %{content_type} %{size_download}", url],
                       capture_output=True, text=True, env=ENV)
    return (r.stdout or "").strip()


def local_pages():
    return sorted(f for f in os.listdir(SITE)
                  if f.endswith(".html") and not f.startswith("_"))


PAGES = local_pages()

# ---- wait for the rebuild to pick up the new commit -----------------------
print("waiting for Pages to serve the latest commit...")
probe = "index.html"
want = hashlib.sha256(open(os.path.join(SITE, probe), "rb").read()).hexdigest()
for i in range(40):
    got = hashlib.sha256(raw(BASE + probe)).hexdigest()
    if got == want:
        print("  latest commit is live (%s matches byte for byte)\n" % probe)
        break
    time.sleep(15)
else:
    print("  TIMEOUT waiting for the rebuild")
    fails.append("live site did not reach the latest commit")

print("--- 1. pages ---")
ok_pages = set()
for p in PAGES:
    c = head(BASE + p)
    ok = c.startswith("200")
    if ok:
        ok_pages.add(p)
    else:
        fails.append("page %s -> %s" % (p, c))
    print("  %s %-24s %s" % ("OK " if ok else "FAIL", p, c))

print("\n--- 2. assets (every reference on every page) ---")
assets = set()
for p in PAGES:
    html = raw(BASE + p).decode("utf-8", errors="replace")
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html):
        v = m.group(1)
        if v.endswith(".html") or v.startswith("data:") or v.startswith("#"):
            continue
        assets.add(v)
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
    if p not in ok_pages:
        continue                      # a 404 body is GitHub's own page, not ours
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
if cdn:
    fails.append("external CDN dependency")

print("\n--- 8. live page set == repo page set ---")
linked = set(re.findall(r'href="([^"#?]+\.html)"', idx))
linked |= {m.group(1) for p in PAGES for m in
           [re.search(r'href="([^"#?]+\.html)"', raw(BASE + p).decode("utf-8", "replace"))] if m}
live_set = {p for p in linked if "/" not in p}
missing = sorted(set(PAGES) - live_set)
stale = sorted(live_set - set(PAGES))
print("  pages in repo : %d  %s" % (len(PAGES), ", ".join(PAGES)))
print("  linked on live: %d  %s" % (len(live_set), ", ".join(sorted(live_set))))
if missing:
    print("  NOT LINKED:", missing)
    fails.append("pages not linked from the live site: %s" % missing)
if stale:
    print("  STALE LINKS:", stale)
    fails.append("stale page links on the live site: %s" % stale)
if not missing and not stale:
    print("  OK  every page is reachable and no page is left over")

print("\n" + "=" * 60)
print("RESULT:", "ALL CHECKS PASSED" if not fails else "FAILURES: %s" % fails)
sys.exit(0 if not fails else 1)
