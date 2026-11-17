"""Contact sheets + manifest for the newly created folders in D:\\photo.

set1 刚开始接触相机 / set2 在学校的日常 / set3 旅游 / set4 古庙 / 作者
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = r"D:\photo"
OUT = r"D:\minimax_work\_tools\contact3"
os.makedirs(OUT, exist_ok=True)

SETS = ["set1 刚开始接触相机", "set2 在学校的日常", "set3 旅游", "set4 古庙", "作者"]
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def font(sz):
    for c in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"):
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F = font(19)
manifest = {}

for s in SETS:
    folder = os.path.join(ROOT, s)
    if not os.path.isdir(folder):
        print("MISSING", folder)
        continue
    key = s.split()[0]
    files = []
    for fn in sorted(os.listdir(folder)):
        p = os.path.join(folder, fn)
        if os.path.isfile(p) and os.path.splitext(fn)[1].lower() in EXTS:
            files.append((fn, p))

    recs = []
    for fn, p in files:
        try:
            with Image.open(p) as im:
                w, h = im.size
                ex = im.getexif()
                recs.append({"name": fn, "path": p, "w": w, "h": h,
                             "ratio": round(w / h, 3), "orient": ex.get(274),
                             "bytes": os.path.getsize(p)})
        except Exception as e:
            print("ERR", fn, e)

    manifest[key] = {"label": s, "items": recs}
    print("%-4s %-22s %d images" % (key, s, len(recs)))

    COLS, ROWS, TW, TH = 4, 4, 460, 380
    for idx in range(0, max(1, len(recs)), COLS * ROWS):
        chunk = recs[idx:idx + COLS * ROWS]
        sheet = Image.new("RGB", (COLS * TW, ROWS * TH), (16, 16, 18))
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            gi = idx + i
            cx, cy = (i % COLS) * TW, (i // COLS) * TH
            try:
                with Image.open(r["path"]) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    im.thumbnail((TW - 14, TH - 46), Image.LANCZOS)
                    sheet.paste(im, (cx + (TW - im.width) // 2, cy + 36 + (TH - 46 - im.height) // 2))
            except Exception:
                pass
            d.text((cx + 8, cy + 8), "%s#%02d %s" % (key, gi, r["name"][:32]),
                   fill=(255, 232, 110), font=F)
            d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline=(70, 70, 78))
        sheet.save(os.path.join(OUT, "%s_sheet_%02d.jpg" % (key, idx // (COLS * ROWS))), quality=86)
        print("   sheet", key, idx // (COLS * ROWS))

json.dump(manifest, open(os.path.join(OUT, "manifest3.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n--- detail ---")
for key, v in manifest.items():
    print("### %s  (%s)" % (key, v["label"]))
    for i, r in enumerate(v["items"]):
        print("  %s#%02d  %-46s %5dx%-5d ratio %s" % (key, i, r["name"], r["w"], r["h"], r["ratio"]))
