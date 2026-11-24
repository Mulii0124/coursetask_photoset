"""
Asset pipeline v3 — 木離 QIANJINGJING photography portfolio.

Source: the photographer's own folders inside D:\\photo, created as the final
curation of this portfolio:

    set1 刚开始接触相机    14 frames
    set2 在学校的日常       16 frames
    set3 旅游             16 frames
    set4 古庙              9 frames
    作者                   1 frame   (author portrait)

set1 also contains eight `retouch_*.jpg` files: those are a photography studio's
own summer-set samples (they carry the "Pe.Daphine vortex 2023" watermark and
show the studio's album display and a model). They were not shot by the
photographer, but they do belong to that folder, so they are kept — as the
clearly labelled second half of the "begin" series, behind a SPLITS divider —
instead of being passed off as her own work.

One editorial grade is applied so that phone, Olympus and drone frames from
four different years read as a single commissioned set. Output: progressive
JPEG at three widths plus a 24px blurred placeholder per image.
"""
import base64
import io
import json
import os
import shutil

from PIL import Image, ImageEnhance, ImageOps

def _find_site():
    """Locate the site root from wherever this script lives.

    The script is kept in two places — the working copy in ``_tools/`` and a
    tracked copy inside the repository at ``site/tools/`` — so the site root is
    discovered instead of hard-coded.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    cands = []
    for _ in range(4):
        cands.append(d)
        cands.append(os.path.join(d, "site"))
        d = os.path.dirname(d)
    for c in cands:
        if os.path.isfile(os.path.join(c, "assets", "css", "site.css")):
            return c
    raise SystemExit("cannot locate the site root (assets/css/site.css)")


SITE = _find_site()

# The photographer's own folders. Override with PHOTO_ROOT if they move.
PHOTO_ROOT = os.environ.get("PHOTO_ROOT", r"D:\photo")

SET_DIRS = {
    "S1": os.path.join(PHOTO_ROOT, "set1 刚开始接触相机"),
    "S2": os.path.join(PHOTO_ROOT, "set2 在学校的日常"),
    "S3": os.path.join(PHOTO_ROOT, "set3 旅游"),
    "S4": os.path.join(PHOTO_ROOT, "set4 古庙"),
    "AU": os.path.join(PHOTO_ROOT, "作者"),
}

# ------------------------------------------------------------------ series ---
SERIES = [
    {
        "slug": "begin", "num": "01",
        "cn": "初", "en": "BEGINNING", "title_en": "Learning to Press the Shutter",
        "year": "2022—2023", "place": "起步 · 街巷与水边", "place_en": "FIRST LIGHT / STREETS & WATER",
        "cover": "S1_03",
        "lead": "第一批照片没有构图，也没有主题。\n"
                "有一只坐在干草里的猫，有夜里从高处看下去的城市灯网，"
                "有一个写着「40」的限速牌，一张被电线切开的天空，"
                "还有一池被倒过来的柳。\n"
                "我按拍下来的顺序把它们放在一起——那顺序本身就是我学会看的时间线。\n"
                "卷末还压着八张不是我拍的照片：影楼寄修时附回来的样片。"
                "它们单独成卷，来路写在卷二的标题下面。",
        "lead_en": "The first roll had no composition and no theme.\n"
                   "A cat in dry grass. A city seen from above at night. "
                   "A speed limit sign. A sky cut open by wires. A pool with the willows upside down.\n"
                   "I keep them in the order I shot them — that order is the timeline of learning to see.\n"
                   "At the end of the roll sit eight frames I did not shoot: samples that came back "
                   "with the studio's prints. They get a volume of their own, with their origin stated.",
        "note": "手记 · 第一卷：还没有构图的时候",
    },
    {
        "slug": "days", "num": "02",
        "cn": "日", "en": "DAYS", "title_en": "The Ordinary Hours",
        "year": "2023", "place": "校园 · 树与光", "place_en": "CAMPUS / TREES & LIGHT",
        "cover": "S2_14",
        "lead": "学校是一间很大的暗房。\n"
                "绣球开在树荫下面，银杏把整条路点着，操场边的下午很长，"
                "黄昏的云一直压在校舍的屋顶上。\n"
                "我在这里拍了一年零散的日常，直到承认日常本身就是一种题材。",
        "lead_en": "A campus is a very large darkroom.\n"
                   "Hydrangeas under the shade, ginkgo lighting up the whole avenue, "
                   "long afternoons by the field, and a cloud sitting low on the school roof.\n"
                   "I shot loose fragments here for a year before admitting that the everyday "
                   "is a subject in its own right.",
        "note": "手记 · 校园是一间大暗房",
    },
    {
        "slug": "journey", "num": "03",
        "cn": "旅", "en": "JOURNEY", "title_en": "Farther Than the Map",
        "year": "2026", "place": "远方 · 一段长途", "place_en": "ELSEWHERE / A LONG WAY",
        "cover": "S3_11",
        "lead": "出发的第二天，我开始不再找构图，只是看。\n"
                "鹿在公园里低头，石庭的沙被耙成一圈一圈，"
                "傍晚的堤上有人背对着水坐着。\n"
                "这些照片没有主题，只有距离——距离是唯一值得带回来的东西。",
        "lead_en": "By the second day I stopped looking for compositions and simply looked.\n"
                   "A deer lowering its head in the park; sand raked into circles in a stone garden; "
                   "someone sitting on the sea wall with their back to the water.\n"
                   "These frames have no theme, only distance — and distance is the only "
                   "thing worth bringing back.",
        "note": "手记 · 不再找构图的那几天",
    },
    {
        "slug": "temple", "num": "04",
        "cn": "庙", "en": "TEMPLE", "title_en": "Under the Eaves",
        "year": "2023", "place": "古庙 · 檐下与香", "place_en": "TEMPLE / EAVES & INCENSE",
        "cover": "S4_01",
        "lead": "屋檐把天空切成一条缝，鸟从缝里穿过去。\n"
                "香炉前的金色莲花摆得很整齐，风一吹，枝上的红灯笼就跟着晃。\n"
                "这些庙我前后去过几次，每次都在同一个位置停下来——等那束光从瓦缝里落下来。",
        "lead_en": "The eaves cut the sky into a slit, and the birds pass through it.\n"
                   "The golden lotus flowers stand in neat rows before the incense burner; "
                   "when the wind comes, the red lanterns move with it.\n"
                   "I have photographed these temples several times and always stop in the same "
                   "place — waiting for the light to come down between the tiles.",
        "note": "手记 · 等一束光落下来",
    },
]

# (source_id, ordinal, caption_cn, caption_en)
# source_id: "S<n>_<idx>" = D:\photo\set<n> …, "AU_00" = D:\photo\作者
PLATES = {
    "begin": [
        ("S1_03", "01", "水中的柳", "A willow in the water"),
        ("S1_01", "02", "夜里的城", "The city at night"),
        ("S1_00", "03", "猫", "A cat"),
        ("S1_02", "04", "限速四十", "Forty kilometres"),
        ("S1_04", "05", "被电线切开的天空", "A sky cut by wires"),
        ("S1_05", "06", "石头上的孩子", "A child on the stone"),
        ("S1_06", "07", "白花", "White blossoms"),
        ("S1_07", "08", "松针与光", "Pine needles in the sun"),
        ("S1_08", "09", "树下", "Under the trees"),
        ("S1_09", "10", "园墙", "The garden wall"),
        ("S1_10", "11", "花树", "A flowering tree"),
        ("S1_11", "12", "花束", "A bouquet"),
        ("S1_12", "13", "相册陈列", "The studio album wall"),
        ("S1_13", "14", "花摊", "A flower stall"),
    ],
    "days": [
        ("S2_14", "01", "绣球", "Hydrangea"),
        ("S2_05", "02", "晚照", "Sunset through the clouds"),
        ("S2_03", "03", "树影与天空", "Trees against the sky"),
        ("S2_06", "04", "云", "Cloud over the roof"),
        ("S2_15", "05", "灯市", "Lanterns and balloons"),
        ("S2_11", "06", "银杏", "Ginkgo"),
        ("S2_12", "07", "逆光的银杏", "Ginkgo, backlit"),
        ("S2_10", "08", "波斯菊", "Cosmos"),
        ("S2_13", "09", "河与城市", "River and city"),
        ("S2_01", "10", "操场边的下午", "An afternoon by the field"),
        ("S2_02", "11", "天桥", "The overpass"),
        ("S2_04", "12", "窗台上的水盆", "Basins by the window"),
        ("S2_00", "13", "桌上的画", "A drawing on the desk"),
        ("S2_07", "14", "田野与电塔", "Fields and pylons"),
        ("S2_08", "15", "路牌与树", "The sign and the tree"),
        ("S2_09", "16", "秋", "Autumn"),
    ],
    "journey": [
        ("S3_11", "01", "塔", "Pagoda"),
        ("S3_06", "02", "十字路口", "The scramble"),
        ("S3_05", "03", "铁塔", "The tower"),
        ("S3_00", "04", "街与塔", "A street and a tower"),
        ("S3_01", "05", "城", "The castle, in black and white"),
        ("S3_02", "06", "两杯冰咖啡", "Two iced coffees"),
        ("S3_03", "07", "鹿", "A deer"),
        ("S3_04", "08", "街角", "A corner abroad"),
        ("S3_07", "09", "石庭", "Stones and sand"),
        ("S3_08", "10", "海港", "The waterfront"),
        ("S3_09", "11", "湖边", "At the lake"),
        ("S3_10", "12", "木栏", "At the wooden rail"),
        ("S3_12", "13", "青柚", "A green fruit"),
        ("S3_13", "14", "长椅上", "On the bench"),
        ("S3_14", "15", "河口", "The river mouth"),
        ("S3_15", "16", "海边的路", "Road along the sea"),
    ],
    "temple": [
        ("S4_01", "01", "檐与群鸟", "Eaves and a flock"),
        ("S4_07", "02", "逆光的灯笼", "Lanterns, backlit"),
        ("S4_06", "03", "黄灯笼与梅", "Yellow lanterns and plum"),
        ("S4_08", "04", "梅枝与池", "Plum over the pond"),
        ("S4_00", "05", "飞檐", "The flying eave"),
        ("S4_02", "06", "鸟群", "Birds in the sky"),
        ("S4_03", "07", "层檐", "Layered eaves"),
        ("S4_04", "08", "香与莲", "Incense and lotus"),
        ("S4_05", "09", "竹林", "Bamboo"),
    ],
}

# A text divider inserted before the given plate index, for the point where a
# series changes character part-way through.
#   SPLITS[slug] = (plate index, {eyebrow, title, cn, en})
SPLITS = {
    "begin": (6, {
        "eyebrow": "卷二 / PART TWO",
        "title": "影楼样片",
        "cn": "这八张是影楼寄修时附回来的样片，每一张上都烧着"
              "「Pe.Daphine vortex 2023」的水印。\n"
              "它们不是我拍的。留在这一卷里，是因为它们本来就躺在这个文件夹中——"
              "与其假装没有，不如把来路写清楚。",
        "en": "These eight frames came back with the studio's prints, every one of "
              "them burned with the \"Pe.Daphine vortex 2023\" watermark.\n"
              "They are not mine. They stay in this roll because they were already in "
              "the folder — better to say where they came from than to leave them out.",
    }),
}

# full-bleed / special images
HERO = "S2_05"      # light on the corrugated wall
STORY = "S4_07"     # backlit lanterns under the branches
PORTRAIT = "AU_00"  # the photographer, from behind, by the water


def build_catalog():
    cat = {}
    for prefix, folder in SET_DIRS.items():
        if not os.path.isdir(folder):
            raise SystemExit("missing source folder: %s" % folder)
        names = sorted(f for f in os.listdir(folder)
                       if os.path.isfile(os.path.join(folder, f))
                       and os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".png", ".webp"))
        for i, fn in enumerate(names):
            cat["%s_%02d" % (prefix, i)] = {"name": fn, "path": os.path.join(folder, fn)}
    return cat


def grade(im, mode):
    if mode == "mono":
        im = ImageOps.grayscale(im).convert("RGB")
    else:
        im = ImageEnhance.Color(im).enhance(0.94)
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Brightness(im).enhance(1.01)
    if mode == "mono":
        r, g, b = im.split()
        r = r.point(lambda v: min(255, int(v * 1.015 + 4)))
        g = g.point(lambda v: min(255, int(v * 1.005 + 2)))
        b = b.point(lambda v: min(255, int(v * 0.985 + 1)))
        im = Image.merge("RGB", (r, g, b))
    return im


def is_mono(im):
    px = im.resize((40, 40)).getdata()
    return all(abs(p[0] - p[2]) <= 7 for p in px)


def save(im, path, width, quality):
    w, h = im.size
    if w > width:
        im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return os.path.getsize(path)


def lqip(im):
    t = im.copy()
    t.thumbnail((24, 24), Image.LANCZOS)
    buf = io.BytesIO()
    t.save(buf, "JPEG", quality=42)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    cat = build_catalog()
    lqips = {}
    total = 0
    n = 0

    def emit(sid, rel, width, quality, force=None):
        nonlocal total, n
        rec = cat[sid]
        im = ImageOps.exif_transpose(Image.open(rec["path"])).convert("RGB")
        mode = force or ("mono" if is_mono(im) else "color")
        im = grade(im, mode)
        size = save(im, os.path.join(SITE, rel), width, quality)
        lqips[rel] = lqip(im)
        total += size
        n += 1
        print("  %-46s %6.0f KB  %s" % (rel, size / 1024, mode))
        return im

    print("== series plates ==")
    for s in SERIES:
        for sid, ordn, _cn, _en in PLATES[s["slug"]]:
            emit(sid, "assets/img/%s/%s-%s.jpg" % (s["slug"], s["slug"], ordn), 1800, 79)

    print("== series covers ==")
    for s in SERIES:
        emit(s["cover"], "assets/img/%s/cover-%s.jpg" % (s["slug"], s["slug"]), 1400, 79)

    print("== full bleed ==")
    emit(HERO, "assets/img/cover/hero.jpg", 2600, 78, force="color")
    emit(STORY, "assets/img/cover/story.jpg", 2600, 78)
    emit(PORTRAIT, "assets/img/cover/portrait.jpg", 1200, 82)

    out = os.path.join(SITE, "assets", "img", "lqip.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lqips, f, ensure_ascii=False, indent=0)

    print("\n%d files, %.1f MB" % (n, total / 1048576))


if __name__ == "__main__":
    main()
