"""Compare live Pages files against the local repository working tree (byte-exact).

The file list is discovered from the local repository, so it always describes
what is actually published.
"""
import hashlib
import os
import subprocess

BASE = "https://mulii0124.github.io/coursetask_photoset/"
ENV = dict(os.environ, HTTP_PROXY="http://127.0.0.1:8899", HTTPS_PROXY="http://127.0.0.1:8899")


def find_repo():
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(4):
        for c in (d, os.path.join(d, "site")):
            if os.path.isfile(os.path.join(c, "assets", "css", "site.css")):
                return os.path.normpath(c)
        d = os.path.dirname(d)
    raise SystemExit("cannot locate the site root (assets/css/site.css)")


REPO = find_repo()

# every html page + css + js + nojekyll, discovered from the repo
FILES = []
for root, dirs, names in os.walk(REPO):
    dirs[:] = [x for x in dirs if x not in (".git", "tools", "__pycache__")]
    for n in names:
        if n.startswith("_"):
            continue
        rel = os.path.relpath(os.path.join(root, n), REPO).replace("\\", "/")
        if rel.endswith((".html", ".css", ".js")) or n == ".nojekyll":
            FILES.append(rel)
FILES.sort()

bad = []
for rel in FILES:
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", BASE + rel],
                       capture_output=True, env=ENV)
    live = r.stdout
    local = open(os.path.join(REPO, rel.replace("/", os.sep)), "rb").read()
    same = hashlib.sha256(live).hexdigest() == hashlib.sha256(local).hexdigest()
    print("%-30s live=%-8d local=%-8d identical=%s" % (rel, len(live), len(local), same))
    if not same:
        bad.append(rel)
        for i in range(min(len(live), len(local))):
            if live[i] != local[i]:
                print("    first diff at byte %d" % i)
                print("    live : %r" % live[max(0, i - 60):i + 60])
                print("    local: %r" % local[max(0, i - 60):i + 60])
                break
        else:
            print("    one is a prefix of the other")

print("\n" + "=" * 60)
print("RESULT:", "LIVE MATCHES REPO" if not bad else "DIFFERS: %s" % bad)
