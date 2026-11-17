"""Dump EXIF (camera model, capture time, size) for every source frame."""
import os

from PIL import Image
from PIL.ExifTags import TAGS

FOLDERS = [
    ("S1", r"D:\photo\set1 刚开始接触相机"),
    ("S2", r"D:\photo\set2 在学校的日常"),
    ("S3", r"D:\photo\set3 旅游"),
    ("S4", r"D:\photo\set4 古庙"),
    ("AU", r"D:\photo\作者"),
]


def main():
    for label, folder in FOLDERS:
        names = sorted(f for f in os.listdir(folder)
                       if os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".png", ".webp"))
        print("=== %s  (%d frames) ===" % (label, len(names)))
        for i, fn in enumerate(names):
            p = os.path.join(folder, fn)
            bits = []
            try:
                with Image.open(p) as im:
                    ex = im.getexif() or {}
                    d = {TAGS.get(k, k): v for k, v in ex.items()}
                    make = str(d.get("Make", "")).strip()
                    model = str(d.get("Model", "")).strip()
                    if make or model:
                        bits.append("%s %s" % (make, model))
                    dt = str(d.get("DateTimeOriginal") or d.get("DateTime") or "")
                    if dt:
                        bits.append(dt)
                    bits.append("%dx%d" % im.size)
            except Exception as e:
                bits.append("ERR %s" % e)
            print("  %s_%02d  %-44s %s" % (label, i, fn[:44], " | ".join(bits)))


if __name__ == "__main__":
    main()
