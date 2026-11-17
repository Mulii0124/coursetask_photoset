"""
Labelled contact sheet of the *built* assets, so every caption can be checked
against the frame it actually belongs to.

    python _tools\label_sheet.py
    -> _tools/shots/label-sheet.jpg
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"D:\minimax_work\_tools")
from build_assets import PLATES, SERIES  # noqa: E402

ROOT = r"D:\minimax_work"
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "_tools", "shots", "label-sheet.jpg")

COLS = 6
CELL_W, CELL_H = 300, 250
PAD = 8
LABEL_H = 46

try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
    FONT_S = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
except Exception:
    FONT = ImageFont.load_default()
    FONT_S = ImageFont.load_default()


def cell(img_rel, top, bottom):
    im = Image.open(os.path.join(SITE, img_rel)).convert("RGB")
    im.thumbnail((CELL_W - PAD * 2, CELL_H - LABEL_H - PAD * 2), Image.LANCZOS)
    card = Image.new("RGB", (CELL_W, CELL_H), (245, 244, 241))
    x = (CELL_W - im.width) // 2
    y = PAD
    card.paste(im, (x, y))
    d = ImageDraw.Draw(card)
    d.text((PAD, y + im.height + 4), top, font=FONT, fill=(20, 20, 20))
    d.text((PAD, y + im.height + 22), bottom, font=FONT_S, fill=(110, 105, 95))
    return card


def main():
    items = []
    for s in SERIES:
        slug = s["slug"]
        for sid, ordn, cn, en in PLATES[slug]:
            rel = "assets/img/%s/%s-%s.jpg" % (slug, slug, ordn)
            items.append((slug, sid, ordn, cn, en, rel))

    per_page = 24
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for p in range((len(items) + per_page - 1) // per_page):
        chunk = items[p * per_page:(p + 1) * per_page]
        rows = []
        for i in range(0, len(chunk), COLS):
            row = []
            for slug, sid, ordn, cn, en, rel in chunk[i:i + COLS]:
                row.append(cell(rel, "%s %s  %s" % (ordn, cn, sid), en))
            rows.append(row)
        W = COLS * CELL_W
        H = len(rows) * CELL_H
        sheet = Image.new("RGB", (W, H), (255, 255, 255))
        for ri, row in enumerate(rows):
            for ci, c in enumerate(row):
                sheet.paste(c, (ci * CELL_W, ri * CELL_H))
        out = OUT.replace(".jpg", "-%d.jpg" % (p + 1))
        sheet.save(out, "JPEG", quality=86)
        print("wrote %s  (%dx%d)" % (out, W, H))


if __name__ == "__main__":
    main()
