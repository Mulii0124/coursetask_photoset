"""
Site generator — 木離 QIANJINGJING photography portfolio.

Emits a self-contained static site into site/:
    index.html  works.html  series-garden.html  series-lantern.html
    series-sky.html  series-street.html  series-journey.html
    journal.html  about.html  contact.html

Every link and asset reference is relative. No absolute paths, no file://.
"""
import json
import os
from PIL import Image

ROOT = r"D:\minimax_work"
SITE = os.path.join(ROOT, "site")

import sys
sys.path.insert(0, r"D:\minimax_work\_tools")
from build_assets import SERIES, PLATES   # noqa: E402

NAME_CN = "木離"
NAME_EN = "QIANJINGJING"
YEAR_FROM, YEAR_TO = "2023", "2026"

PAGES = [
    ("index.html", "首页"),
    ("works.html", "作品"),
    ("series-garden.html", "01 园"),
    ("series-lantern.html", "02 灯"),
    ("series-sky.html", "03 天"),
    ("series-street.html", "04 街"),
    ("series-journey.html", "05 旅"),
    ("journal.html", "手记"),
    ("about.html", "关于"),
    ("contact.html", "联系"),
]

# ---------------------------------------------------------------- helpers ---


def dims(rel):
    p = os.path.join(SITE, rel)
    with Image.open(p) as im:
        return im.size


def ratio_class(w, h):
    r = w / float(h)
    if r >= 1.55:
        return "wide"
    if r >= 1.05:
        return "std"
    return "tall"


def img(rel, alt, css="", extra="", cls="", lazy=True):
    w, h = dims(rel)
    loading = ' decoding="async"' if lazy else ' decoding="async" fetchpriority="high"'
    c = (" " + cls) if cls else ""
    e = (" " + extra) if extra else ""
    return '<img src="%s" alt="%s" width="%d" height="%d"%s%s%s>' % (rel, alt, w, h, loading, c, e)


def head(title, desc, page):
    extra = ""
    if page == "index.html":
        extra = ('\n    <link rel="preload" as="image" href="assets/img/cover/hero.jpg" '
                 'fetchpriority="high">\n'
                 '    <link rel="preload" as="font" type="font/woff2" '
                 'href="assets/fonts/anton-latin-400-normal.woff2" crossorigin>')
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — %s %s</title>
<meta name="description" content="%s">
<meta name="author" content="%s %s">
<meta name="theme-color" content="#0a0a0b">
<meta property="og:title" content="%s — %s %s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<link rel="stylesheet" href="assets/css/site.css">%s
</head>
<body class="page-%s">
<div class="curtain" aria-hidden="true"><span class="curtain__mark">%s</span></div>
""" % (title, NAME_CN, NAME_EN, desc, NAME_CN, NAME_EN, title, NAME_CN, NAME_EN, desc, extra, page, NAME_EN)


def nav(page):
    links = []
    for href, label in PAGES:
        if href in ("index.html", "works.html", "journal.html", "about.html", "contact.html"):
            cur = ' aria-current="page"' if href == page else ""
            links.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return """<nav class="nav" aria-label="主导航">
  <div class="nav__inner">
    <a class="nav__brand" href="index.html">%s <b>%s</b></a>
    <button class="nav__toggle" aria-expanded="false" aria-label="打开菜单"><span></span><span></span><span></span></button>
    <div class="nav__links">
      %s
    </div>
  </div>
</nav>
""" % (NAME_CN, NAME_EN, "\n      ".join(links))


def footer():
    series_links = []
    for s in SERIES:
        series_links.append('<a href="series-%s.html">%s %s</a>' % (s["slug"], s["num"], s["cn"]))
    return """<footer class="foot">
  <div class="u-wrap">
    <div class="foot__top">
      <div>
        <p class="foot__name">%s <b>%s</b></p>
        <p class="foot__role">Photography · 摄影作品集 · %s—%s</p>
      </div>
      <div class="foot__cols">
        <div class="foot__col">
          <b>作品 / Works</b>
          <a href="works.html">作品总览</a>
          %s
        </div>
        <div class="foot__col">
          <b>页面 / Pages</b>
          <a href="index.html">首页</a>
          <a href="journal.html">拍摄手记</a>
          <a href="about.html">摄影师介绍</a>
          <a href="contact.html">联系与合作</a>
        </div>
      </div>
    </div>
    <div class="foot__bottom">
      <span>© <span data-year>2026</span> %s %s · 保留所有权利</span>
      <span>所有影像由摄影师拍摄与处理 / All frames shot &amp; edited by the photographer</span>
    </div>
  </div>
</footer>
<script src="assets/js/site.js"></script>
</body>
</html>
""" % (NAME_CN, NAME_EN, YEAR_FROM, YEAR_TO, "\n          ".join(series_links), NAME_CN, NAME_EN)


def page(title, desc, page, body, extra_class=""):
    out = head(title, desc, page)
    out += nav(page)
    out += body
    out += footer()
    if extra_class:
        out = out.replace('<body class="page-%s">' % page, '<body class="page-%s %s">' % (page, extra_class))
    return out


def write(name, content):
    path = os.path.join(SITE, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("  %-28s %6.1f KB" % (name, len(content.encode("utf-8")) / 1024))


# ------------------------------------------------------------ components ---


def plate(slug, idx, layout="full", extra_class=""):
    """One image plate with its caption."""
    sid, ordn, cn, en = PLATES[slug][idx]
    rel = "assets/img/%s/%s-%s.jpg" % (slug, slug, ordn)
    w, h = dims(rel)
    rc = ratio_class(w, h)

    if layout == "duo":
        return ""
    frame_cls = "plate__frame plate__frame--%s" % rc
    cap = ('<div class="plate__cap"><b>%s</b><span>%s</span></div>' % (cn, en))
    return """<div class="u-wrap u-max">
<figure class="plate %s" data-reveal="up">
  <div class="%s">%s</div>
  %s
</figure>
</div>""" % (extra_class, frame_cls, img(rel, cn), cap)


def duo(slug, i, j):
    out = []
    for k in (i, j):
        sid, ordn, cn, en = PLATES[slug][k]
        rel = "assets/img/%s/%s-%s.jpg" % (slug, slug, ordn)
        w, h = dims(rel)
        rc = ratio_class(w, h)
        out.append("""<figure class="plate__item" data-reveal="up">
  <div class="plate__frame plate__frame--%s">%s</div>
  <div class="plate__cap"><b>%s</b><span>%s</span></div>
</figure>""" % (rc, img(rel, cn), cn, en))
    return """<div class="u-wrap u-max">
<div class="duo" style="margin-block:clamp(70px,13vh,170px)">
  %s
</div>
</div>""" % "\n  ".join(out)


def series_page(s):
    slug = s["slug"]
    n = len(PLATES[slug])
    parts = []

    # ---- header -------------------------------------------------------
    parts.append("""<section class="section on-ink" style="padding-top:clamp(120px,18vh,200px)">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">系列 %s / SERIES %s</span>
      <h1 class="cn-display" style="font-size:clamp(3.4rem,14vw,12rem);letter-spacing:.12em">%s</h1>
      <p class="section__latin">%s — %s</p>
    </div>
    <div style="display:grid;grid-template-columns:minmax(0,1fr);gap:clamp(22px,3.4vw,48px);max-width:74ch">
      <p class="lead-cn" data-reveal="up">%s</p>
      <p class="lead-en" data-reveal="up">%s</p>
    </div>
    <div style="display:flex;gap:clamp(18px,3vw,44px);flex-wrap:wrap;margin-top:clamp(24px,4vh,44px);font-size:.68rem;letter-spacing:.24em;text-transform:uppercase;color:var(--dim)" data-reveal="up">
      <span>年份 / %s</span>
      <span>地点 / %s</span>
      <span>帧数 / %d</span>
      <span>介质 / DIGITAL</span>
    </div>
  </div>
</section>""" % (s["num"], s["num"], s["cn"], s["en"], s["title_en"],
                 s["lead"].replace("\n", "<br>"), s["lead_en"],
                 s["year"], s["place"], n))

    # ---- plates, interleaved with text --------------------------------
    quote = ('<blockquote class="quote" data-reveal="up">%s</blockquote>'
             % s["note"].replace("手记 · ", ""))
    plan = [
        ("full", 0, ""),
        ("text", None, quote),
        ("offset", 1, "plate--offset"),
        ("duo", (2, 3), ""),
        ("full", 4, ""),
        ("offsetleft", 5, "plate--offset-left"),
        ("full", 6, ""),
        ("duo", (7, 8), ""),
        ("offset", 9, "plate--offset"),
        ("full", 10, ""),
    ]
    used = set()
    for kind, idx, cls in plan:
        if kind == "text":
            parts.append('<section class="section on-ink" style="padding-block:0">\n  <div class="u-wrap u-max">%s</div>\n</section>' % cls)
            continue
        if kind == "duo":
            a, b = idx
            if a >= n or b >= n:
                continue
            parts.append(duo(slug, a, b))
            used.update((a, b))
            continue
        if idx >= n:
            continue
        parts.append(plate(slug, idx, "full", cls))
        used.add(idx)

    # ---- remaining plates ---------------------------------------------
    rest = [i for i in range(n) if i not in used]
    for i in rest:
        cls = "plate--offset" if i % 2 else ""
        parts.append(plate(slug, i, "full", cls))

    # ---- next series --------------------------------------------------
    idxs = [s["slug"] for s in SERIES]
    nxt = SERIES[(idxs.index(slug) + 1) % len(SERIES)]
    parts.append("""<section class="section on-paper" style="padding-block:clamp(60px,9vh,120px)">
  <div class="u-wrap u-max">
    <div style="display:flex;align-items:baseline;justify-content:space-between;gap:24px;flex-wrap:wrap;border-top:1px solid var(--rule-ink);padding-top:clamp(22px,3vh,38px)">
      <div>
        <span class="eyebrow">下一个系列 / NEXT SERIES %s</span>
        <p class="cn-display" style="font-size:clamp(1.8rem,4.4vw,3.6rem);letter-spacing:.14em;margin-top:10px">%s</p>
      </div>
      <a class="btn btn--ink" href="series-%s.html"><span>进入 %s</span><span class="btn__arrow">→</span></a>
    </div>
  </div>
</section>""" % (nxt["num"], nxt["cn"], nxt["slug"], nxt["en"]))

    body = "\n".join(parts)
    desc = "%s %s 系列 — %s。%s" % (NAME_CN, s["cn"], s["title_en"], s["lead"].replace("\n", " "))
    return page("%s %s" % (s["num"], s["cn"]), desc, "series-%s.html" % slug, body)


# ----------------------------------------------------------------- pages ---


def build_index():
    s = SERIES
    cat_items = []
    for x in s:
        cat_items.append("""<li><button class="cat__item%s" data-series data-src="assets/img/%s/cover-%s.jpg" data-alt="%s %s" data-cap-cn="%s · %s" data-cap-en="%s" data-cap-no="%s">
          <span class="cat__num">%s</span>
          <span class="cat__cn">%s</span>
          <span class="cat__meta">%s <i>·</i> %s</span>
        </button></li>""" % (
            " is-active" if x is s[0] else "",
            x["slug"], x["slug"], x["cn"], x["title_en"], x["cn"], x["place"], x["en"], x["num"],
            x["num"], x["cn"], x["year"], x["place"]))

    locs = "".join(
        """<div class="locations__cell"><b>%s</b><span>%s</span><em>%s</em></div>"""
        % (x["num"], x["place"], x["cn"]) for x in s)

    body = """
<section class="pin">
  <div class="pin__stage">
    <div class="hero">
      <div class="hero__media">%s</div>
      <div class="hero__body">
        <span class="eyebrow hero__eyebrow" data-reveal="down">摄影作品集 · PHOTOGRAPHY COLLECTION · %s—%s</span>
        <h1 class="hero__title" data-reveal="up">停在<em>光</em>里</h1>
        <p class="hero__latin" data-reveal="up">Still Here</p>
        <div class="hero__rule"></div>
        <div class="hero__foot">
          <p class="hero__statement" data-reveal="up">五个系列，关于光如何落在一个地方——园林、庙会、屋脊、街道，以及一次长途的旅行。<br>Five series on the way light lands in a place.</p>
          <div class="hero__actions" data-reveal="up">
            <a class="btn btn--accent" href="works.html"><span>查看作品</span><span class="btn__arrow">→</span></a>
            <a class="btn" href="#catalogue"><span>本页系列目录</span><span class="btn__arrow">↓</span></a>
          </div>
        </div>
      </div>
      <div class="scroll-cue">向下滚动 / SCROLL</div>
    </div>
  </div>
</section>

<section class="section on-paper" id="catalogue">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">01 — 精选作品 / SELECTED SERIES</span>
      <h2 class="section__title">系列目录</h2>
      <p class="section__latin">Five series · %s—%s</p>
    </div>
    <div class="cat">
      <ol class="cat__list" role="listbox" aria-label="系列目录" data-reveal="up">
        %s
      </ol>
      <div class="cat__stage">
        <figure class="slot" data-slot>
          %s
          %s
        </figure>
        <figcaption class="cat__cap" data-cap></figcaption>
      </div>
    </div>
  </div>
</section>

<section class="section on-ink interlude">
  <div class="u-wrap u-max">
    <div class="interlude__grid">
      <p class="statement statement--wide" data-reveal="up">我拍的不是地方，<br>是<em>光落在地方上的方式</em>。</p>
      <p class="lead-en" data-reveal="up">I am not photographing places. I am photographing the way light lands on them — and how long it is willing to stay.</p>
    </div>
    <div class="locations" data-reveal="up">%s</div>
    <div class="notes" style="margin-top:clamp(46px,8vh,96px)">
      <div class="note" data-reveal="up">
        <span class="note__no">NOTE 01</span>
        <h4>关于等待</h4>
        <p>我通常比现场的人早到半小时。不是为了抢光，而是为了看清一个地方在没有人的时候是什么样子。</p>
      </div>
      <div class="note" data-reveal="up">
        <span class="note__no">NOTE 02</span>
        <h4>关于黑白</h4>
        <p>黑不是去掉颜色，是让形状自己说话。鸟、屋脊、闪电——这些题材一旦去色，轮廓会更狠。</p>
      </div>
      <div class="note" data-reveal="up">
        <span class="note__no">NOTE 03</span>
        <h4>关于修图</h4>
        <p>每张照片统一做一次对比与饱和的校准，让不同时间、不同机器拍的东西看起来像同一次展览。</p>
      </div>
    </div>
  </div>
</section>

<section class="story">
  <div class="story__media">%s</div>
  <div class="story__body">
    <div class="u-wrap u-max">
      <span class="eyebrow" data-reveal="up">02 — 重点故事 / KEY STORY</span>
      <h2 class="story__title" data-reveal="up" style="margin-top:14px">庙会第三夜，风把两盏灯吹到了同一根枝上。</h2>
      <div class="story__meta" data-reveal="up">
        <span>灯 / LANTERN</span><span>2023</span><span>北方 · 庙会</span><span>第 01 帧 / 12</span>
      </div>
      <p class="lead-en" data-reveal="up" style="margin-top:22px">On the third night of the fair the wind moved two lanterns onto the same branch. The sun was already behind the roof, and everything that remained was borrowed light.</p>
    </div>
  </div>
</section>

<section class="section on-paper" id="about">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">03 — 摄影师介绍 / THE PHOTOGRAPHER</span>
      <h2 class="section__title">%s %s</h2>
      <p class="section__latin">About the photographer</p>
    </div>
    <div class="profile">
      <figure class="profile__portrait" data-reveal="up">
        %s
        <figcaption>人物 · 石缝 / FIGURE IN THE ROCK · 2023</figcaption>
      </figure>
      <div class="profile__text">
        <h3 data-reveal="up">创作理念</h3>
        <p data-reveal="up">我的起点很具体：一个人在一条街的尽头站着，光从侧面来。于是我开始等光，而不是等地点。<br>拍照对我来说更像一种记录习惯——同一个地方我会反复回去，直到它开始认出我。</p>
        <h3 data-reveal="up">经历</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>2022</b><span>开始使用可换镜头相机记录校园与周边，尝试把「练习」变成「系列」</span></div>
          <div class="cv__row"><b>2023</b><span>完成「园」「灯」两组系列，建立统一的对比与色彩校准流程</span></div>
          <div class="cv__row"><b>2024</b><span>开始为画面加入更多人物与叙事元素，「街」系列成形</span></div>
          <div class="cv__row"><b>2026</b><span>第一次长线远行，完成「旅」系列与航拍部分</span></div>
          <div class="cv__row"><b>NOW</b><span>在做「园」的十年计划——同一处园林，每年同一个窗口回去一次</span></div>
        </div>
        <p data-reveal="up" style="margin-top:28px"><a class="btn btn--ink" href="about.html"><span>完整介绍</span><span class="btn__arrow">→</span></a></p>
      </div>
    </div>
  </div>
</section>
""" % (
        img("assets/img/cover/hero.jpg", "夜色中倒映在水面的城市灯光", lazy=False),
        YEAR_FROM, YEAR_TO,
        YEAR_FROM, YEAR_TO,
        "\n        ".join(cat_items),
        img("assets/img/garden/cover-garden.jpg", "园 · 江南园林", lazy=False),
        img("assets/img/lantern/cover-lantern.jpg", "灯 · 庙会"),
        locs,
        img("assets/img/cover/story.jpg", "逆光中的红色灯笼与树枝", lazy=False),
        NAME_CN, NAME_EN,
        img("assets/img/cover/portrait.jpg", "石缝中的人物", lazy=False),
    )
    return page("摄影作品集", "%s %s 摄影作品集：园林、庙会、屋脊、街道与一次长途的旅行，%s—%s。" % (NAME_CN, NAME_EN, YEAR_FROM, YEAR_TO), "index.html", body)


def build_works():
    blocks = []
    for x in SERIES:
        n = len(PLATES[x["slug"]])
        blocks.append("""<article class="work">
  <a class="work__media" href="series-%s.html" aria-label="进入 %s 系列">%s</a>
  <div>
    <div class="work__meta"><b>%s</b><span>%s</span><span>%s</span></div>
    <h2 class="work__title"><a href="series-%s.html">%s</a></h2>
    <p class="work__latin">%s — %s</p>
    <p class="work__text">%s</p>
    <a class="work__more" href="series-%s.html">进入系列 / VIEW SERIES</a>
  </div>
</article>""" % (x["slug"], x["cn"],
                 img("assets/img/%s/cover-%s.jpg" % (x["slug"], x["slug"]), "%s 系列 · %s" % (x["cn"], x["place"])),
                 x["num"], x["year"], x["place"],
                 x["slug"], x["cn"],
                 x["en"], x["title_en"],
                 x["lead"].replace("\n", " "),
                 x["slug"]))

    body = """
<section class="section on-ink" style="padding-top:clamp(120px,18vh,200px)">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">作品 / WORKS</span>
      <h1 class="cn-display" style="font-size:clamp(2.8rem,10vw,8rem);letter-spacing:.1em">全部作品</h1>
      <p class="section__latin">Five series · %s—%s</p>
    </div>
    <div class="works">
      %s
    </div>
  </div>
</section>
""" % (YEAR_FROM, YEAR_TO, "\n      ".join(blocks))
    desc = "%s %s 全部作品：%s。" % (NAME_CN, NAME_EN, "、".join(x["cn"] for x in SERIES))
    return page("作品", desc, "works.html", body)


def build_journal():
    entries = [
        ("01", "2023.03", "江南 · 园林", "第一组园林照片，是在等一场不会来的雨。",
         "三月的江南多雨，我从第一次带相机出门起就在等雨。那天雨一直没下，我就一直坐在廊下看光线从砖地移到假山上。\n"
         "后来我明白，等不到雨的时候才是最好的部分——没有戏剧性，只有缓慢移动的影子。\n"
         "这一组照片大多是这样来的：没有事件，只有时间。",
         "assets/img/garden/garden-01.jpg", "绣球 · 六月的第一周"),
        ("02", "2023.08", "北方 · 庙会", "庙会的光是人造的，所以它结束得也很快。",
         "庙会只有三天。我连去三天，第三天把相机挂在了腰上，几乎没有举起来——那些逆光的画面，靠的是站的位置，不是技巧。\n"
         "夜里十一点，人开始散，灯还亮着。那一刻的画面比白天好，因为没有人再挡光。",
         "assets/img/lantern/lantern-01.jpg", "逆光 · 灯"),
        ("03", "2024.05", "城中 · 街道", "我把城市拍成了一张水面的倒影。",
         "有一晚下过雨之后，我在便利店门口站了很久，最后只拍了一张水面上的灯光倒影。\n"
         "那张照片后来成了「街」系列的封面。它提醒我：最像一座城市的，未必是它的建筑。",
         "assets/img/street/street-08.jpg", "夜的水面"),
        ("04", "2024.09", "城郊 · 屋脊", "鸟比天气预报更早知道要下雨。",
         "屋脊上的鸟群是我一整年反复拍的题材。开始我拍它们飞的样子，后来才拍到它们停下来的样子。\n"
         "停下来才是更难的那一张。",
         "assets/img/sky/sky-02.jpg", "群鸟"),
        ("05", "2026.08", "远方 · 街市", "第一次带着无人机的八天。",
         "出发前两周才开始研究航拍规则，落地后才发现大多数地方根本不能飞。\n"
         "于是那八天里，大部分照片还是在地面上拍的——这反而更像我习惯的方式。\n"
         "唯一一次飞起来是在海边，风很大，飞机差点没回来。",
         "assets/img/journey/journey-13.jpg", "水中的门"),
        ("06", "2026.08", "远方 · 海岸", "航班延误四小时，于是有了云上的那张照片。",
         "原本要坐的那班飞机晚点了四个小时，我在候机楼的窗边拍下了云层。\n"
         "后来整理照片时发现，这张在地面拍的云，比我在高空拍的所有海面都好。",
         "assets/img/journey/journey-15.jpg", "白花与远山"),
    ]
    blocks = []
    for no, date, place, title, body, img_rel, cap in entries:
        blocks.append("""<article class="entry">
  <div class="entry__side" data-reveal="up">
    <b>%s</b>
    <span>%s</span>
    <span>%s</span>
  </div>
  <div class="entry__body">
    <h3 data-reveal="up">%s</h3>
    <p data-reveal="up">%s</p>
    <figure data-reveal="up">%s<figcaption>%s</figcaption></figure>
  </div>
</article>""" % (no, date, place, title, body.replace("\n", "<br>"), img(img_rel, cap), cap))

    body = """
<section class="section on-paper" style="padding-top:clamp(120px,18vh,200px)">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">手记 / FIELD NOTES</span>
      <h1 class="cn-display" style="font-size:clamp(2.8rem,10vw,8rem);letter-spacing:.1em">拍摄手记</h1>
      <p class="section__latin">Notes from the field · %s—%s</p>
    </div>
    <div class="journal__list">
      %s
    </div>
  </div>
</section>
""" % (YEAR_FROM, YEAR_TO, "\n      ".join(blocks))
    desc = "%s %s 的拍摄手记：关于等待、黑白、修图与远行。" % (NAME_CN, NAME_EN)
    return page("拍摄手记", desc, "journal.html", body)


def build_about():
    body = """
<section class="section on-paper" style="padding-top:clamp(120px,18vh,200px)">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">关于 / THE PHOTOGRAPHER</span>
      <h1 class="cn-display" style="font-size:clamp(2.6rem,9vw,7rem);letter-spacing:.1em">%s %s</h1>
      <p class="section__latin">%s · Photography since 2022</p>
    </div>
    <div class="profile">
      <figure class="profile__portrait" data-reveal="up">
        %s
        <figcaption>人物 · 石缝 / FIGURE IN THE ROCK · 2023</figcaption>
      </figure>
      <div class="profile__text">
        <h3 data-reveal="up">创作理念</h3>
        <p data-reveal="up">我的起点很具体：一个人在一条街的尽头站着，光从侧面来。于是我开始等光，而不是等地点。<br>
        我不拍「风景」，我拍光落下来的方式——它停在哪一块砖上，哪一片叶子被穿过去，哪一瞬间屋脊上的鸟全部离开。<br>
        所以我的照片常常没有人在画面中心，但总有一处正在被照亮。</p>
        <p data-reveal="up">我的方法很笨：同一个地方反复回去，每年同一个窗口，不同的天气。拍到第三年，那个地方开始有我的痕迹，
        我也开始能预判它的光。十个系列的「园」就是这个计划的第一次尝试。</p>

        <h3 data-reveal="up">经历</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>2022</b><span>开始使用可换镜头相机记录校园与周边，尝试把「练习」变成「系列」</span></div>
          <div class="cv__row"><b>2023</b><span>完成「园」「灯」两组系列，建立统一的对比与色彩校准流程</span></div>
          <div class="cv__row"><b>2024</b><span>开始为画面加入更多人物与叙事元素，「街」系列成形</span></div>
          <div class="cv__row"><b>2025</b><span>系统整理 2022—2024 的全部底片，按主题重新归入五个系列</span></div>
          <div class="cv__row"><b>2026</b><span>第一次长线远行，完成「旅」系列与航拍部分</span></div>
          <div class="cv__row"><b>NOW</b><span>在做「园」的十年计划——同一处园林，每年同一个窗口回去一次</span></div>
        </div>

        <h3 data-reveal="up">工作方式与器材</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>机身</b><span>奥林巴斯可换镜头相机（室内与手持主力）</span></div>
          <div class="cv__row"><b>航拍</b><span>DJI 微型无人机（2026 年旅途中开始使用）</span></div>
          <div class="cv__row"><b>后期</b><span>统一对比度与饱和度校准；黑白题材单独暖调处理</span></div>
          <div class="cv__row"><b>归档</b><span>每个系列一个文件夹，文件名统一为「系列-序号」，与本页目录对应</span></div>
        </div>

        <p data-reveal="up" style="margin-top:28px">
          <a class="btn btn--ink" href="works.html"><span>看全部作品</span><span class="btn__arrow">→</span></a>
          <a class="btn btn--ink" href="contact.html" style="margin-left:12px"><span>联系与合作</span><span class="btn__arrow">→</span></a>
        </p>
      </div>
    </div>
  </div>
</section>
""" % (NAME_CN, NAME_EN, NAME_EN,
       img("assets/img/cover/portrait.jpg", "石缝中的人物", lazy=False))
    desc = "%s %s：摄影理念、创作经历与工作方式。" % (NAME_CN, NAME_EN)
    return page("摄影师介绍", desc, "about.html", body)


def build_contact():
    body = """
<section class="section on-paper" style="padding-top:clamp(120px,18vh,200px)">
  <div class="u-wrap u-max">
    <div class="section__head" data-reveal="up">
      <span class="eyebrow section__index">联系 / CONTACT</span>
      <h1 class="cn-display" style="font-size:clamp(2.6rem,9vw,7rem);letter-spacing:.1em">联系与合作</h1>
      <p class="section__latin">Available for editorial &amp; licensing</p>
    </div>
    <div class="contact">
      <div class="contact__cards" data-reveal="up">
        <div class="contact__card">
          <b>电子邮件 / Email</b>
          <a href="mailto:1945004760@qq.com">1945004760@qq.com</a>
          <button class="copy" data-copy="1945004760@qq.com" type="button">复制邮箱</button>
        </div>
        <div class="contact__card">
          <b>代码与作品 / GitHub</b>
          <a href="https://github.com/Mulii0124" target="_blank" rel="noopener">github.com/Mulii0124</a>
        </div>
        <div class="contact__card">
          <b>所在地 / Based in</b>
          <span>武汉 · 中国 / Wuhan, China</span>
        </div>
        <div class="contact__card">
          <b>可承接 / Available for</b>
          <span>画册与出版 / 展览拍摄 / 影像授权</span>
        </div>
      </div>

      <form class="composer" data-composer="1945004760@qq.com" data-reveal="up">
        <div class="composer__row">
          <label for="c-name">你的称呼 / Your name</label>
          <input id="c-name" name="name" type="text" autocomplete="name" placeholder="如何称呼你">
        </div>
        <div class="composer__row">
          <label for="c-subject">主题 / Subject</label>
          <input id="c-subject" name="subject" type="text" placeholder="例如：杂志专题拍摄 / 作品授权">
        </div>
        <div class="composer__row">
          <label for="c-msg">内容 / Message</label>
          <textarea id="c-msg" name="message" placeholder="简单说说你的需求与时间"></textarea>
        </div>
        <button class="btn btn--ink" type="submit"><span>发送邮件</span><span class="btn__arrow">→</span></button>
        <p class="composer__note" data-composer-note>点击后将调用你的邮件客户端并自动填好内容；也可以直接复制上方的邮箱地址。</p>
      </form>
    </div>
  </div>
</section>
"""
    desc = "联系 %s %s：合作、出版与影像授权。" % (NAME_CN, NAME_EN)
    return page("联系与合作", desc, "contact.html", body)


# ------------------------------------------------------------------ main ---

def main():
    os.makedirs(SITE, exist_ok=True)
    print("building pages:")
    write("index.html", build_index())
    write("works.html", build_works())
    for s in SERIES:
        write("series-%s.html" % s["slug"], series_page(s))
    write("journal.html", build_journal())
    write("about.html", build_about())
    write("contact.html", build_contact())

    with open(os.path.join(SITE, ".nojekyll"), "w", encoding="utf-8", newline="\n") as f:
        f.write("")
    print("done.")


if __name__ == "__main__":
    main()
