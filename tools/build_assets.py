"""
Asset pipeline v2 — 木離 QIANJINGJING photography portfolio.

Two audited sources:
  P<idx>  D:\\photo                     (own camera / phone frames)
  T<idx>  D:\\photo\\日本旅行照片合集     (2026 Japan trip, drone + phone)

Applies one unified editorial grade so 60+ frames from two bodies read as a
single commissioned set, then exports web-optimised progressive JPEGs plus
24px blurred placeholders (LQIP) for the catalogue.
"""
import base64
import io
import json
import os
from PIL import Image, ImageOps, ImageEnhance

ROOT = r"D:\minimax_work"
SITE = os.path.join(ROOT, "site")
M_LOCAL = r"D:\minimax_work\_tools\contact2\manifest2.json"
M_TRAVEL = r"D:\minimax_work\_tools\contact\manifest.json"

# ------------------------------------------------------------------ series ---
SERIES = [
    {
        "slug": "garden", "num": "01",
        "cn": "园", "en": "GARDEN", "title_en": "A Season in the Garden",
        "year": "2023", "place": "江南 · 园林", "place_en": "JIANGNAN / GARDEN",
        "cover": "P33",
        "lead": "园林是一种被安排过的自然。梅先开，绣球后至，银杏把整条走廊烧成金色。\n"
                "我花了三年时间记录这种顺序——花不是同时盛开的，季节也不是。",
        "lead_en": "A garden is nature with an order imposed on it. Plum first, hydrangea after, "
                   "and ginkgo burning the whole corridor gold.\nThree years went into recording that order: "
                   "flowers never open all at once, and neither do seasons.",
        "note": "手记 · 第 41 页：绣球开了七次，我拍了六次。",
    },
    {
        "slug": "lantern", "num": "02",
        "cn": "灯", "en": "LANTERN", "title_en": "Everything the Sun Leaves Behind",
        "year": "2023", "place": "北方 · 庙会", "place_en": "NORTH / TEMPLE FAIR",
        "cover": "P36",
        "lead": "灯是临时造出来的太阳。\n庙会那几天，天黑得比往常早，人把光挂到树上，"
                "于是树也亮起来——像一场短暂的、可以被收回的白天。",
        "lead_en": "Lanterns are suns made on loan. During the fair, night arrives early; "
                   "people hang light in the trees, and for a few hours the trees keep their own daytime.\n"
                   "It is a temporary day, and it can be taken back down.",
        "note": "手记 · 庙会第三夜，风把两盏灯吹到了同一根枝上。",
    },
    {
        "slug": "sky", "num": "03",
        "cn": "天", "en": "SKY", "title_en": "Birds, Weather, Concrete",
        "year": "2022—2023", "place": "城郊 · 屋脊", "place_en": "OUTSKIRTS / ROOFLINES",
        "cover": "P34",
        "lead": "我拍屋顶上的鸟拍了一年。\n它们比人更早决定天气：云压低，鸟先走；风转向，鸟最后动。",
        "lead_en": "I photographed the birds on the rooflines for a full year.\n"
                   "They decide the weather before we do: when the cloud drops the birds leave first; "
                   "when the wind turns, the birds move last.",
        "note": "手记 · 一张闪电拍了六次，第五次才有形状。",
    },
    {
        "slug": "street", "num": "04",
        "cn": "街", "en": "STREET", "title_en": "The City, Briefly",
        "year": "2022—2023", "place": "城中 · 街道", "place_en": "CITY / STREET LEVEL",
        "cover": "P23",
        "lead": "城市只在晚上承认自己在发光。\n白天它是一堆建筑，夜里倒过来，变成水面上的一团碎光。",
        "lead_en": "A city only admits it is glowing after dark.\nBy day it is a heap of buildings; "
                   "by night it turns into a handful of broken lights on water.",
        "note": "手记 · 那晚没带相机，回来用手机拍下了水面的倒影。",
    },
    {
        "slug": "journey", "num": "05",
        "cn": "旅", "en": "JOURNEY", "title_en": "Eight Days, Five Places",
        "year": "2026", "place": "远方 · 五个地方", "place_en": "ON THE ROAD / FIVE PLACES",
        "cover": "T53",
        "lead": "2026 年 8 月，八天，五个地方。\n"
                "这一组是按地点编号而不是按时间排列的——离开之后，"
                "时间会重新排列地点。",
        "lead_en": "August 2026. Eight days, five places.\nThis set is ordered by location rather than by date, "
                   "because once you leave, time rearranges the places for you.",
        "note": "手记 · 航班延误四小时，于是有了那张云上的照片。",
    },
]

# (source_id, ordinal, caption_cn, caption_en, extra_note)
# source_id: "P<n>" = D:\photo, "T<n>" = 日本旅行照片合集
PLATES = {
    "garden": [
        ("P33", "01", "绣球", "Hydrangea, first week of June"),
        ("P31", "02", "银杏·逆光", "Ginkgo, backlit"),
        ("P30", "03", "银杏", "Ginkgo, full canopy"),
        ("P26", "04", "竹林", "Bamboo"),
        ("P27", "05", "水边的树", "A tree at the water's edge"),
        ("P41", "06", "梅枝与池", "Plum over the pond"),
        ("P2",  "07", "粉色花枝", "Pink blossom, out of focus"),
        ("P38", "08", "梅", "Plum, close"),
        ("P3",  "09", "白梅", "White plum"),
        ("P0",  "10", "郁金香", "Tulips"),
        ("P29", "11", "波斯菊", "Cosmos"),
        ("P8",  "12", "落花", "Fallen petals"),
    ],
    "lantern": [
        ("P39", "01", "逆光·灯", "Lanterns, backlit"),
        ("P36", "02", "黄灯笼与梅", "Yellow lanterns and plum"),
        ("P43", "03", "枝上的灯", "Lanterns in the branches"),
        ("P40", "04", "红灯", "Red lanterns"),
        ("P44", "05", "蓝天下的灯", "Lanterns against blue"),
        ("P35", "06", "灯市", "The lantern fair"),
        ("P24", "07", "飞檐", "Eaves"),
        ("P22", "08", "斗拱", "Bracket sets"),
        ("P19", "09", "暮色", "Dusk on a wall"),
        ("P15", "10", "屋脊上的群鸟", "Birds over the roof"),
        ("P5",  "11", "石门", "Stone gate"),
        ("P1",  "12", "老屋", "Old houses"),
    ],
    "sky": [
        ("P34", "01", "松", "Pine against grey"),
        ("P20", "02", "群鸟", "The flock"),
        ("P28", "03", "树", "Trees"),
        ("P18", "04", "天上的鸟", "Birds in open sky"),
        ("P16", "05", "闪电", "Lightning"),
        ("P17", "06", "闪电 II", "Lightning, second frame"),
        ("P37", "07", "树与天", "Trees and sky"),
        ("P13", "08", "树冠", "Canopy"),
        ("P12", "09", "天桥", "Overpass"),
        ("P10", "10", "公园的下午", "An afternoon in the park"),
        ("P11", "11", "街道与树", "Street and trees"),
        ("P21", "12", "田野", "Field"),
    ],
    "street": [
        ("P23", "01", "石缝里的人", "Figure in the rock"),
        ("P7",  "02", "路口", "The crossing"),
        ("P4",  "03", "猫", "A cat"),
        ("P32", "04", "河与城市", "River and city"),
        ("P42", "05", "湖石上的人", "Figure on the stone"),
        ("P14", "06", "窗台上的蓝", "Blue on the sill"),
        ("P25", "07", "金", "Gold vessels"),
        ("P6",  "08", "夜的水面", "Night water"),
    ],
    "journey": [
        ("T7",   "01", "商店街的彩帘", "Market streamers"),
        ("T8",   "02", "纸垂", "Paper streamers"),
        ("T16",  "03", "寺门", "The temple gate"),
        ("T28",  "04", "鹿与人", "Deer and a stranger"),
        ("T31",  "05", "鹿", "The deer, close"),
        ("T50",  "06", "鹿群", "The herd"),
        ("T53",  "07", "铁塔", "The tower"),
        ("T72",  "08", "十字路口", "The scramble"),
        ("T38",  "09", "雨中的横道", "A crossing in the rain"),
        ("T0",   "10", "雨夜的街口", "A corner in the rain"),
        ("T51",  "11", "杜鹃的坡", "The azalea slope"),
        ("T114", "12", "林中的亭子", "Pavilion"),
        ("T95",  "13", "水中的门", "A gate standing in the water"),
        ("T65",  "14", "机翼与落日", "Wing and sunset"),
        ("T140", "15", "白花与远山", "White flowers and a distant ridge"),
        ("T137", "16", "海边的路", "Road along the water"),
    ],
}

# full-bleed / special images
HERO = ("P6", "cover", "hero")            # night water reflections
STORY = ("P39", "cover", "story")        # backlit lanterns
PORTRAIT = ("P23", "cover", "portrait")  # figure framed by rock
INTERLUDE = ("P26", "cover", "interlude")  # bamboo


def build_catalog():
    cat = {}
    m2 = json.load(open(M_LOCAL, encoding="utf-8"))
    for i, rec in enumerate(m2):
        cat["P%d" % i] = rec
    m1 = json.load(open(M_TRAVEL, encoding="utf-8"))
    for i, rec in enumerate(m1):
        if i < 122 or i >= 128:      # skip the 8.26 assignment folder frames
            cat["T%d" % i] = rec
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
    emit(HERO[0], "assets/img/cover/hero.jpg", 2600, 78)
    emit(STORY[0], "assets/img/cover/story.jpg", 2600, 78)
    emit(PORTRAIT[0], "assets/img/cover/portrait.jpg", 1200, 82)
    emit(INTERLUDE[0], "assets/img/cover/interlude.jpg", 1600, 80)

    out = os.path.join(SITE, "assets", "img", "lqip.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(lqips, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    print("\n%d files, %.1f MB" % (n, total / 1048576))


if __name__ == "__main__":
    main()
