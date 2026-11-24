"""
Site generator — 木離 QIANJINGJING photography portfolio.

Emits a self-contained static site into site/:
    index.html  works.html  series-begin.html  series-days.html
    series-journey.html  series-temple.html
    journal.html  about.html  contact.html

Every link and asset reference is relative. No absolute paths, no file://.
"""
import json
import os
import sys
from PIL import Image


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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_assets import SERIES, PLATES, SPLITS   # noqa: E402

NAME_CN = "木離"
NAME_EN = "QIANJINGJING"
YEAR_FROM, YEAR_TO = "2022", "2026"

PAGES = [
    ("index.html", "首页"),
    ("works.html", "作品"),
    ("series-begin.html", "01 初"),
    ("series-days.html", "02 日"),
    ("series-journey.html", "03 旅"),
    ("series-temple.html", "04 庙"),
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


def img(rel, alt, extra="", cls="", lazy=True):
    w, h = dims(rel)
    loading = ' decoding="async"' if lazy else ' decoding="async" fetchpriority="high"'
    c = (' class="%s"' % cls) if cls else ""
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
      <span>所有影像由摄影师整理与处理 / All frames curated &amp; edited by the photographer</span>
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
<figure class="plate plate--full %s" data-reveal="up">
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

    # ---- a divider where the series changes character ------------------
    split = SPLITS.get(slug)
    split_at = split[0] if split else None
    split_done = [False]

    def divider():
        """Return the divider block once, just before the first split plate."""
        if not split or split_done[0]:
            return ""
        split_done[0] = True
        _at, d = split
        return """<section class="section on-ink" style="padding-block:clamp(46px,8vh,110px)">
  <div class="u-wrap u-max">
    <div class="split" data-reveal="up">
      <span class="eyebrow">%s</span>
      <h3 class="split__title">%s</h3>
      <div style="display:grid;grid-template-columns:minmax(0,1fr);gap:clamp(18px,2.6vw,38px);max-width:74ch">
        <p class="lead-cn">%s</p>
        <p class="lead-en">%s</p>
      </div>
    </div>
  </div>
</section>""" % (d["eyebrow"], d["title"], d["cn"].replace("\n", "<br>"), d["en"])

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
            if split_at is not None and min(a, b) >= split_at:
                parts.append(divider())
            parts.append(duo(slug, a, b))
            used.update((a, b))
            continue
        if idx >= n:
            continue
        if split_at is not None and idx >= split_at:
            parts.append(divider())
        parts.append(plate(slug, idx, "full", cls))
        used.add(idx)

    # ---- remaining plates ---------------------------------------------
    rest = [i for i in range(n) if i not in used]
    for i in rest:
        cls = "plate--offset" if i % 2 else ""
        if split_at is not None and i >= split_at:
            parts.append(divider())
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
        cat_items.append("""<li><a class="cat__item%s" href="series-%s.html" data-series data-src="assets/img/%s/cover-%s.jpg" data-alt="%s %s" data-cap-cn="%s · %s" data-cap-en="%s" data-cap-no="%s">
          <span class="cat__num">%s</span>
          <span class="cat__cn">%s</span>
          <span class="cat__meta">%s <i>·</i> %s</span>
        </a></li>""" % (
            " is-active" if x is s[0] else "",
            x["slug"],
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
        <h1 class="hero__title" data-reveal="up">光有<em>来处</em></h1>
        <p class="hero__latin" data-reveal="up">Where Light Comes From</p>
        <div class="hero__rule"></div>
        <div class="hero__foot">
          <p class="hero__statement" data-reveal="up">四个章节，关于一台相机怎么学会看——第一次按快门、学校的日常、一段长途，以及古庙屋檐下的那束光。<br>Four chapters on how a camera learns to see.</p>
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
      <p class="section__latin">Four series · %s—%s</p>
    </div>
    <div class="cat">
      <ol class="cat__list" aria-label="系列目录" data-reveal="up">
        %s
      </ol>
      <div class="cat__stage">
        <figure class="slot" data-slot>
          %s
          %s
        </figure>        <figcaption class="cat__cap" data-cap></figcaption>
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
        <h4>关于第一次</h4>
        <p>第一批照片没有构图，也没有人教我怎么构图。我把它们按拍下来的顺序排在一起，因为顺序本身就是我学会看的时间线。</p>
      </div>
      <div class="note" data-reveal="up">
        <span class="note__no">NOTE 02</span>
        <h4>关于等待</h4>
        <p>我通常比现场的人早到半小时。不是为了抢光，而是为了看清一个地方在没有人的时候是什么样子。</p>
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
      <h2 class="story__title" data-reveal="up" style="margin-top:14px">庙会那天下午，太阳从两排灯笼中间烧了过去。</h2>
      <div class="story__meta" data-reveal="up">
        <span>庙 / TEMPLE</span><span>2023</span><span>古庙 · 檐下与香</span><span>第 02 帧 / 09</span>
      </div>
      <p class="lead-en" data-reveal="up" style="margin-top:22px">On the afternoon of the temple fair the sun burned its way through the two rows of lanterns. The plum was already out, and the light between them lasted only a few minutes.</p>
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
        <figcaption>人物 · 水边 / FIGURE BY THE WATER · 2026</figcaption>
      </figure>
      <div class="profile__text">
        <h3 data-reveal="up">创作理念</h3>
        <p data-reveal="up">我拍的不是地方，是光落在地方上的方式。<br>
        校园是一间很大的暗房，古庙把天空切成一条缝，长途旅行只教给我一件事：先看，再决定要不要拍。<br>
        所以我的照片常常没有人在画面中心，但总有一处正在被照亮。</p>
        <h3 data-reveal="up">经历</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>2022</b><span>拍下第一批照片——它们没有主题，只有顺序</span></div>
          <div class="cv__row"><b>2023</b><span>校园成为固定拍摄地，完成「日」与「庙」两组系列；同时把影楼附送的样片单独分卷标注</span></div>
          <div class="cv__row"><b>2024</b><span>重心从「拍到」转向「看到」，开始为画面加入人与叙事</span></div>
          <div class="cv__row"><b>2026</b><span>第一次长线远行，完成「旅」系列与航拍部分</span></div>
          <div class="cv__row"><b>NOW</b><span>在做「日」的三年计划——同一处校园，每年同一个窗口回去一次</span></div>
        </div>
        <p data-reveal="up" style="margin-top:28px"><a class="btn btn--ink" href="about.html"><span>完整介绍</span><span class="btn__arrow">→</span></a></p>
      </div>
    </div>
  </div>
</section>
""" % (
        img("assets/img/cover/hero.jpg", "落日从云缝里烧过去，落在学校的楼顶上方", lazy=False),
        YEAR_FROM, YEAR_TO,
        YEAR_FROM, YEAR_TO,
        "\n        ".join(cat_items),
        img("assets/img/begin/cover-begin.jpg", "初 · 水中的柳", extra='data-role="a"', cls="slot__img is-active", lazy=False),
        img("assets/img/days/cover-days.jpg", "日 · 校园的绣球", extra='data-role="b" aria-hidden="true"', cls="slot__img"),
        locs,
        img("assets/img/cover/story.jpg", "逆光中的灯笼与树枝", lazy=False),
        NAME_CN, NAME_EN,
        img("assets/img/cover/portrait.jpg", "坐在水边石堤上的人，手里握着一台相机", lazy=False),
    )
    return page("摄影作品集", "%s %s 摄影作品集：起步、校园日常、一次长途的旅行与古庙，%s—%s。" % (NAME_CN, NAME_EN, YEAR_FROM, YEAR_TO), "index.html", body)


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
      <p class="section__latin">Four series · %s—%s</p>
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
        ("01", "2022—2023", "起步 · 街巷", "第一批照片里有一只猫，我按了快门，然后什么也没想。",
         "相机是借来的，存储卡是最便宜的那种。我不知道该拍什么，就对着能看见的东西按快门。\n"
         "那批照片有一只坐在干草里的猫，有一个写着「40」的限速牌，还有一张被电线切开的天空。\n"
         "后来整理的时候我才发现，我一直在拍同一件事：光落在什么地方。",
         "assets/img/begin/begin-03.jpg", "猫"),
        ("02", "2023", "校园 · 黄昏", "云压得很低，有一条光从云缝里烧过去，我等它烧完。",
         "那是一个傍晚，我在教学楼之间绕了很久，找一个能把天空放进画框的角度。\n"
         "最后停在一堵墙和另一栋楼之间：左边全黑，右边云缝里有一条正在烧完的光。\n"
         "那张照片后来成了整个作品集的开场。我想，拍光就是拍它只剩下几分钟的那段时间。",
         "assets/img/days/days-02.jpg", "晚照"),
        ("03", "2023.09", "古庙 · 檐下", "鸟从屋檐的缝隙里穿过去，那天我一张也没拍到它们停下。",
         "同一天上午我还在校园里拍过一片田野，到了下午，人已经在另一座庙的檐下。\n"
         "屋檐把天空切成一条很窄的缝，鸟群从缝里过。我举着相机等了四十分钟，\n"
         "拍到的全是飞行中的一团影子，没有一张是停住的。\n"
         "后来我才明白，鸟不下来才是那座庙真正的样子。",
         "assets/img/temple/temple-01.jpg", "檐与群鸟"),
        ("04", "2023", "校园 · 银杏", "银杏把整条路点着，我拍了六次才拍到没有人的那一张。",
         "银杏最好看的那天也是人最多的那天。我换了三个位置、五个时间，\n"
         "最后选的是早上七点，整条路是金的，只有扫地的阿姨在画面边缘。\n"
         "她没有抬头，那张也没有。",
         "assets/img/days/days-06.jpg", "银杏"),
        ("05", "2026.08", "远方 · 街市", "出发的第二天，我不再找构图，只是看。",
         "第一天的照片全是地标，很努力，很一般。\n"
         "第二天下雨，我在便利店门口坐着，看鹿在公园里低头，看路口的车灯把雨照成两条线。\n"
         "我一张也没有拍。那天晚上整理，决定只留三张。",
         "assets/img/journey/journey-02.jpg", "十字路口"),
        ("06", "2026.08", "远方 · 水边", "最后一张是在堤上拍的，无人机在包里，没有拿出来。",
         "相机包里还剩一台微型无人机，那天海边风很大，没有起飞。\n"
         "我就坐在堤上，看一个人背对着水拍照，看了很久。\n"
         "后来那张背影也成了这一组里我最喜欢的一张。",
         "assets/img/journey/journey-11.jpg", "湖边"),
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
    desc = "%s %s 的拍摄手记：关于第一次、等待、黑白、修图与远行。" % (NAME_CN, NAME_EN)
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
        <figcaption>人物 · 水边 / FIGURE BY THE WATER · 2026</figcaption>
      </figure>
      <div class="profile__text">
        <h3 data-reveal="up">创作理念</h3>
        <p data-reveal="up">我不拍「风景」，我拍光落下来的方式——它停在哪一块砖上，哪一片叶子被穿过去，哪一瞬间屋檐上的鸟全部离开。<br>
        校园是一间很大的暗房；古庙把天空切成一条缝；长途旅行只教给我一件事：先看，再决定要不要拍。<br>
        所以我的照片常常没有人在画面中心，但总有一处正在被照亮。</p>
        <p data-reveal="up">我的方法很笨：同一个地方反复回去，每年同一个窗口，不同的天气。拍到第三年，那个地方开始有我的痕迹，
        我也开始能预判它的光。「日」系列的三年计划就是这个方法的第一次正式尝试。</p>

        <p data-reveal="up">「初」这一卷里也留了八张不是我拍的照片——那是影楼寄修时附回来的样片，画面上烧着他们的水印。
        我没有把它们删掉，也没有把它们混进自己的作品里，而是在卷二里单独标出来。整理素材和诚实地标注素材，同样是创作的一部分。</p>

        <h3 data-reveal="up">经历</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>2022</b><span>拍下第一批照片——它们没有主题，只有顺序</span></div>
          <div class="cv__row"><b>2023</b><span>校园成为固定拍摄地，完成「日」与「庙」两组系列；同时把影楼附送的样片单独分卷标注</span></div>
          <div class="cv__row"><b>2024</b><span>重心从「拍到」转向「看到」，开始为画面加入人与叙事</span></div>
          <div class="cv__row"><b>2025</b><span>系统整理全部底片，按四个主题重新归组（set1—set4）</span></div>
          <div class="cv__row"><b>2026</b><span>第一次长线远行，完成「旅」系列与航拍部分</span></div>
          <div class="cv__row"><b>NOW</b><span>在做「日」的三年计划——同一处校园，每年同一个窗口回去一次</span></div>
        </div>

        <h3 data-reveal="up">工作方式与器材</h3>
        <div class="cv" data-reveal="up">
          <div class="cv__row"><b>机身</b><span>奥林巴斯 E-M10（校园、古庙与远行的主力）</span></div>
          <div class="cv__row"><b>手机</b><span>OPPO A9x 拍下 2022 年的第一批；iPhone 拍下 2026 年路上的随手拍</span></div>
          <div class="cv__row"><b>航拍</b><span>DJI Mini 微型无人机（2026 年旅途中开始使用，也拍下了那张水边的人物照）</span></div>
          <div class="cv__row"><b>后期</b><span>统一对比度与饱和度校准；黑白题材单独暖调处理</span></div>
          <div class="cv__row"><b>归档</b><span>按主题分成 set1—set4 四个文件夹，与本页目录一一对应</span></div>
          <div class="cv__row"><b>标注</b><span>非本人拍摄的素材单独分卷，并注明来路</span></div>
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
       img("assets/img/cover/portrait.jpg", "坐在水边石堤上的人，手里握着一台相机", lazy=False))
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
          <a href="#composer" data-mail="1945004760@qq.com">1945004760@qq.com</a>
          <button class="copy" data-copy="1945004760@qq.com" type="button" aria-label="复制邮箱地址">邮箱</button>
        </div>
        <div class="contact__card">
          <b>代码与作品 / GitHub</b>
          <span>github.com/Mulii0124</span>
          <button class="copy" data-copy="github.com/Mulii0124" data-copy-prefix="https://" type="button" aria-label="复制仓库地址">仓库地址</button>
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

      <form class="composer" id="composer" data-composer="1945004760@qq.com" data-reveal="up">
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
