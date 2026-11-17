"""Contact sheets for the D:\\photo root files (excluding the already-scanned 日本旅行照片合集 subdir)."""
import os, json
from PIL import Image, ImageOps, ImageDraw, ImageFont

SRC = r"D:\photo"
OUT = r"D:\minimax_work\_tools\contact2"
os.makedirs(OUT, exist_ok=True)

def font(sz):
    for c in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"):
        if os.path.exists(c):
            try: return ImageFont.truetype(c, sz)
            except Exception: pass
    return ImageFont.load_default()

F = font(20)
files = []
for fn in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, fn)
    if not os.path.isfile(p): continue
    if os.path.splitext(fn)[1].lower() not in (".jpg", ".jpeg", ".png", ".webp"): continue
    files.append((fn, p))

recs = []
for fn, p in files:
    try:
        with Image.open(p) as im:
            w, h = im.size
            ex = im.getexif()
            recs.append({"name": fn, "path": p, "w": w, "h": h, "ratio": round(w/h,2),
                         "orient": ex.get(274), "date": ex.get(36867) or ex.get(306)})
    except Exception as e:
        print("ERR", fn, e)

json.dump(recs, open(os.path.join(OUT, "manifest2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL", len(recs))

COLS, ROWS, TW, TH = 5, 4, 400, 320
idx = 0
for start in range(0, len(recs), COLS*ROWS):
    chunk = recs[start:start+COLS*ROWS]
    sheet = Image.new("RGB", (COLS*TW, ROWS*TH), (16,16,18))
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(chunk):
        gi = start + i
        cx, cy = (i % COLS)*TW, (i // COLS)*TH
        try:
            with Image.open(r["path"]) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((TW-12, TH-42), Image.LANCZOS)
                sheet.paste(im, (cx+(TW-im.width)//2, cy+32+(TH-42-im.height)//2))
        except Exception: pass
        d.text((cx+8, cy+6), "#%03d %s" % (gi, r["name"][:34]), fill=(255,232,110), font=F)
        d.rectangle([cx, cy, cx+TW-1, cy+TH-1], outline=(66,66,74))
    sheet.save(os.path.join(OUT, "p_sheet_%02d.jpg" % idx), quality=84)
    print("sheet", idx)
    idx += 1

for i, r in enumerate(recs):
    print(i, r["name"], r["w"], "x", r["h"], "ratio", r["ratio"], "orient", r["orient"])
