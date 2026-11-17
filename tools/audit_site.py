"""
Audit the generated site:
  · every href/src must be relative (no http(s)://, no file://, no leading /)
  · every local target must exist on disk
  · every page must be reachable from index.html
  · report image dimensions that are missing
"""
import os
import re
from html.parser import HTMLParser

SITE = r"D:\minimax_work\site"
HTML = [f for f in os.listdir(SITE) if f.lower().endswith(".html")]

REF = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I)
CSS_URL = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)
CSS_IMPORT = re.compile(r'@import\s+(?:url\()?["\']([^"\']+)', re.I)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.imgs = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "img":
            self.imgs.append(d)
        if tag == "a":
            self.links.append(d)


def check_rel(ref, where, problems):
    low = ref.lower()
    if low.startswith(("http://", "https://", "file://", "//", "data:", "mailto:", "tel:", "#")):
        return None                      # external / non-file reference
    if ref.startswith("/"):
        problems.append("ABSOLUTE ROOT PATH  %-40s  in %s" % (ref, where))
        return None
    if re.match(r"^[A-Za-z]:[\\/]", ref):
        problems.append("ABSOLUTE DRIVE PATH %-40s  in %s" % (ref, where))
        return None
    return ref


problems = []
all_local = set()

# ---- HTML ------------------------------------------------------------------
index_links = set()
for page in sorted(HTML):
    path = os.path.join(SITE, page)
    src = open(path, encoding="utf-8").read()
    p = P()
    p.feed(src)

    for m in REF.finditer(src):
        ref = m.group(1)
        local = check_rel(ref, page, problems)
        if local:
            all_local.add(local)
            target = os.path.normpath(os.path.join(SITE, local.split("#")[0].split("?")[0]))
            if not os.path.exists(target):
                problems.append("MISSING TARGET       %-40s  in %s" % (ref, page))

    for im in p.imgs:
        if "width" not in im or "height" not in im:
            problems.append("IMG WITHOUT DIMENSIONS %-35s in %s" % (im.get("src", "?"), page))

    for lk in p.links:
        href = lk.get("href", "")
        if href and not href.startswith(("http", "mailto", "#")):
            index_links.add(href.split("#")[0])

# ---- CSS -------------------------------------------------------------------
for root, _dirs, files in os.walk(os.path.join(SITE, "assets", "css")):
    for f in files:
        if not f.endswith(".css"):
            continue
        cpath = os.path.join(root, f)
        css = open(cpath, encoding="utf-8").read()
        for rx in (CSS_URL, CSS_IMPORT):
            for m in rx.finditer(css):
                ref = m.group(1)
                local = check_rel(ref, "assets/css/" + f, problems)
                if local:
                    all_local.add(local)
                    target = os.path.normpath(os.path.join(root, local))
                    if not os.path.exists(target):
                        problems.append("MISSING CSS ASSET    %-40s  in assets/css/%s" % (ref, f))

# ---- reachability ----------------------------------------------------------
idx = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
ip = P()
ip.feed(idx)
reach = set()
for lk in ip.links:
    href = lk.get("href", "")
    if href and not href.startswith(("http", "mailto", "#")):
        reach.add(href.split("#")[0])
missing_pages = [h for h in sorted(HTML) if h != "index.html" and h not in reach]
if missing_pages:
    problems.append("NOT LINKED FROM INDEX: %s" % ", ".join(missing_pages))

# ---- report ----------------------------------------------------------------
print("pages            : %d  (%s)" % (len(HTML), ", ".join(sorted(HTML))))
print("distinct refs    : %d" % len(all_local))
print("linked from index: %d" % len(reach))
print("-" * 78)
if problems:
    print("PROBLEMS (%d):" % len(problems))
    for x in problems:
        print("  " + x)
else:
    print("OK — all references relative, all targets exist, every page reachable.")
print("-" * 78)
print("total site size  : %.1f MB" % (
    sum(os.path.getsize(os.path.join(r, f))
        for r, _d, fs in os.walk(SITE) for f in fs) / 1048576))
