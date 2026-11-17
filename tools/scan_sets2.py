"""EXIF capture dates for the new set folders + a finalist sheet of key candidates."""
import json
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

M3 = json.load(open(r"D:\minimax_work\_tools\contact3\manifest3.json", encoding="utf-8"))
OUT = r"D:\minimax_work\_tools\contact3"

print("=== capture dates ===")
for skey, sv in M3.items():
    print("### %s (%s)" % (skey, sv["label"]))
    for i, r in enumerate(sv["items"]):
        d = ""
        try:
            with Image.open(r["path"]) as im:
                ex = im.getexif()
                d = ex.get(36867) or ex.get(306) or ""
                for sub in (34665,):
                    if not d and ex.get(sub):
                        g = ex.get(sub)
                        d = "%s:%s:%s" % (g.get(306, "")[:10], g.get(307, ""), g.get(36868, ""))
        except Exception as e:
            d = "ERR %s" % e
        print("  %-6s#%02d  %-44s %s" % (skey, i, r["name"][:42], d))

# finalist sheet
CANDS = [
    ("set1", 1, "hero-1 night city"),
    ("set1", 3, "roof ink"),
    ("set1", 5, "girl on rock"),
    ("set2", 5, "light streak"),
    ("set2", 3, "trees sky"),
    ("set2", 13, "city river"),
    ("set2", 15, "balloons"),
    ("set3", 6, "shibuya aerial"),
    ("set3", 5, "tokyo tower"),
    ("set3", 9, "lake person"),
    ("set3", 11, "pavilion"),
    ("set4", 1, "temple birds B&W"),
    ("set4", 7, "lanterns flare"),
    ("set4", 6, "lanterns blossom"),
    ("作者", 0, "AUTHOR"),
]


def font(sz):
    for c in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\msyh.ttc"):
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F = font(22)
COLS, ROWS, TW, TH = 3, 5, 620, 480
sheet = Image.new("RGB", (COLS * TW, ROWS * TH), (14, 14, 16))
d = ImageDraw.Draw(sheet)
for i, (sk, idx, label) in enumerate(CANDS):
    r = M3[sk]["items"][idx]
    cx, cy = (i % COLS) * TW, (i // COLS) * TH
    try:
        with Image.open(r["path"]) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((TW - 16, TH - 54), Image.LANCZOS)
            sheet.paste(im, (cx + (TW - im.width) // 2, cy + 44 + (TH - 54 - im.height) // 2))
    except Exception:
        pass
    d.text((cx + 10, cy + 10), "%s#%02d  %s" % (sk, idx, label), fill=(255, 232, 110), font=F)
    d.rectangle([cx, cy, cx + TW - 1, cy + TH - 1], outline=(70, 70, 78))
sheet.save(os.path.join(OUT, "finalists.jpg"), quality=88)
print("\nfinalist sheet ->", os.path.join(OUT, "finalists.jpg"))
