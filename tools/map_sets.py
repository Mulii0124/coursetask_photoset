"""Map the new set folders onto the old P/T manifest entries, and list what is new."""
import hashlib
import json
import os

M2 = json.load(open(r"D:\minimax_work\_tools\contact2\manifest2.json", encoding="utf-8"))
MT = json.load(open(r"D:\minimax_work\_tools\contact\manifest.json", encoding="utf-8"))
M3 = json.load(open(r"D:\minimax_work\_tools\contact3\manifest3.json", encoding="utf-8"))

OLD = {}
for i, r in enumerate(M2):
    OLD.setdefault((r["name"], r.get("bytes")), []).append("P%d" % i)
for i, r in enumerate(MT):
    OLD.setdefault((r["name"], r.get("bytes")), []).append("T%d" % i)


def key(name, path):
    return (name, os.path.getsize(path))


print("=== new set -> old id ===")
for skey, sv in M3.items():
    for i, r in enumerate(sv["items"]):
        hits = OLD.get(key(r["name"], r["path"]), [])
        print("  %-6s#%02d  %-46s -> %s" % (skey, i, r["name"][:44], ",".join(hits) or "NEW"))

print()
used_ids = set()
for skey, sv in M3.items():
    for r in sv["items"]:
        used_ids.update(OLD.get(key(r["name"], r["path"]), []))

src = open(r"D:\minimax_work\_tools\build_assets.py", encoding="utf-8").read()
import re
block = re.search(r"PLATES\s*=\s*\{(.*?)\n\}", src, re.S).group(1)
old_used = set(re.findall(r'"([PT]\d+)"', block))

print("old curated frames now DROPPED from the site:")
for k in sorted(old_used - used_ids, key=lambda s: (s[0], int(s[1:]))):
    src_i = M2 if k[0] == "P" else MT
    idx = int(k[1:])
    name = src_i[idx]["name"] if idx < len(src_i) else "?"
    print("   %-5s %s" % (k, name))
print()
print("total old curated:", len(old_used), " reused:", len(old_used & used_ids), " dropped:", len(old_used - used_ids))
