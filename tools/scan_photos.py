"""Scan the photo collections: report dimensions, EXIF orientation, GPS, and build contact sheets."""
import os
import json
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont

SRC_DIRS = [
    os.path.expanduser(r"~\Downloads\日本旅行照片合集"),
    os.path.expanduser(r"~\Downloads\8.26新生第三项作业"),
]
OUT_DIR = r"D:\minimax_work\_tools\contact"
os.makedirs(OUT_DIR, exist_ok=True)

records = []
for src in SRC_DIRS:
    if not os.path.isdir(src):
        print("MISSING SRC", src)
        continue
    for fn in sorted(os.listdir(src)):
        p = os.path.join(src, fn)
        if not os.path.isfile(p):
            continue
        if os.path.splitext(fn)[1].lower() not in (".jpg", ".jpeg", ".png", ".webp", ".heic"):
            continue
        try:
            with Image.open(p) as im:
                exif = im.getexif()
                w, h = im.size
                orientation = exif.get(274)
                gps = exif.get_ifd(34853) if hasattr(exif, "get_ifd") else {}
                lat = lon = None
                if gps:
                    try:
                        def dms(v):
                            v = float(v)
                            return v
                        lat = gps.get(2)
                        lon = gps.get(4)
                    except Exception:
                        pass
                records.append({
                    "path": p,
                    "dir": src,
                    "name": fn,
                    "w": w, "h": h,
                    "orient": orientation,
                    "ratio": round(w / h, 3),
                    "bytes": os.path.getsize(p),
                    "gps": bool(lat),
                    "has_exif_date": bool(exif.get(36867)),
                })
        except Exception as e:
            print("ERR", fn, e)

records.sort(key=lambda r: r["name"])
with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=1)

print("TOTAL", len(records))

# Orientation histogram + dimension stats
from collections import Counter
print("ratios", Counter(round(r["ratio"], 1) for r in records).most_common(12))
print("orient", Counter(r["orient"] for r in records))
print("gps", Counter(r["gps"] for r in records))
print("dates", Counter(r["has_exif_date"] for r in records))

# Contact sheets: 5 cols x 4 rows = 20 per sheet, labeled with index
def font(sz):
    for cand in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, sz)
            except Exception:
                pass
    return ImageFont.load_default()

F = font(22)
COLS, ROWS = 5, 4
TW, TH = 380, 300

sheet_idx = 0
for start in range(0, len(records), COLS * ROWS):
    chunk = records[start:start + COLS * ROWS]
    sheet = Image.new("RGB", (COLS * TW, ROWS * TH), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(chunk):
        gi = start + i
        cx, cy = (i % COLS) * TW, (i // COLS) * TH
        try:
            with Image.open(r["path"]) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((TW - 10, TH - 40), Image.LANCZOS)
                sheet.paste(im, (cx + (TW - im.width) // 2, cy + 30 + (TH - 40 - im.height) // 2))
        except Exception:
            pass
        label = "#%03d %s" % (gi, r["name"][:28])
        d.text((cx + 8, cy + 6), label, fill=(255, 235, 120), font=F)
        d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline=(70, 70, 78))
    out = os.path.join(OUT_DIR, "sheet_%02d.jpg" % sheet_idx)
    sheet.save(out, quality=82)
    print("sheet", out)
    sheet_idx += 1
print("DONE")
