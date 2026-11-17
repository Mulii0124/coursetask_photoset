"""Read git blobs as raw bytes (bypassing shell text pipelines)."""
import hashlib
import os
import subprocess

REPO = r"D:\minimax_work\site"

TEXT = ["index.html", "contact.html", "works.html", "journal.html", "about.html",
        "series-garden.html", "series-lantern.html", "series-sky.html",
        "series-street.html", "series-journey.html",
        "assets/css/site.css", "assets/js/site.js", "README.md", ".nojekyll"]
BIN = ["assets/img/cover/hero.jpg", "assets/fonts/anton-latin-400-normal.woff2",
       "assets/img/garden/cover-garden.jpg"]


def blob(ref_path):
    r = subprocess.run(["git", "-C", REPO, "cat-file", "blob", ref_path],
                       capture_output=True)
    return r.stdout


print("--- text blobs (raw) ---")
for p in TEXT:
    b = blob("HEAD:" + p)
    print("%-30s CRLF=%-4d LF=%-5d bytes=%-8d sha=%s" % (
        p, b.count(b"\r\n"), b.count(b"\n"), len(b),
        hashlib.sha256(b).hexdigest()[:12]))

print("\n--- binary blobs vs working tree ---")
for p in BIN:
    b = blob("HEAD:" + p)
    fp = os.path.join(REPO, p.replace("/", os.sep))
    w = open(fp, "rb").read()
    same = hashlib.sha256(b).hexdigest() == hashlib.sha256(w).hexdigest()
    print("%-46s blob=%-8d disk=%-8d identical=%s head=%s" % (
        p, len(b), len(w), same, b[:3]))
