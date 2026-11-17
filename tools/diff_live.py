"""Compare live Pages files against the local repository working tree (byte-exact)."""
import hashlib
import os
import subprocess

REPO = r"D:\minimax_work\site"
BASE = "https://mulii0124.github.io/coursetask_photoset/"
ENV = dict(os.environ, HTTP_PROXY="http://127.0.0.1:8899", HTTPS_PROXY="http://127.0.0.1:8899")

FILES = ["index.html", "works.html", "series-garden.html", "series-lantern.html",
         "series-sky.html", "series-street.html", "series-journey.html",
         "journal.html", "about.html", "contact.html",
         "assets/css/site.css", "assets/js/site.js", ".nojekyll"]

bad = []
for rel in FILES:
    r = subprocess.run(["curl.exe", "-sS", "-L", "--max-time", "60", BASE + rel],
                       capture_output=True, env=ENV)
    live = r.stdout
    local = open(os.path.join(REPO, rel.replace("/", os.sep)), "rb").read()
    same = hashlib.sha256(live).hexdigest() == hashlib.sha256(local).hexdigest()
    print("%-26s live=%-8d local=%-8d identical=%s" % (rel, len(live), len(local), same))
    if not same:
        bad.append(rel)
        # show the first difference
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
