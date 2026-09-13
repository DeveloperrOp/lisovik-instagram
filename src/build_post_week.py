# -*- coding: utf-8 -*-
"""Карусель: товар тижня 14-20.09 — «Енергія і тонус», знижка −20%.

Добірка з чотирьох адаптогенів під одну задачу: кордицепс, мака,
трібулус і женьшень. Так її називає банер самого розділу, і так вона
й подається тут.

🚨 У розділі «Товар тижня» лежить ще курс ENERGY зі знижкою, але в
його коробці мухомор червоний (Amanita muscaria). Мухомор в Instagram
не йде ніколи — категорія Entheogens, і бан прилітає не на пост, а
на весь Business Manager. Тому курс у карусель не входить.

🚨 Правило власника: ПРОДУКТ НА ПЕРШОМУ КАДРІ. Обкладинка — усі
чотири банки в ряд на лісовому тлі.

  1 обкладинка   чотири банки добірки, знижка
  2 що в добірці ціни до і після
  3 кордицепс    легший старт зранку
  4 женьшень     рівна енергія без провалу
  5 мака         макаміди, яких немає ніде
  6 трібулус     наступний день після залу
  7 фінал        строк акції і мокап телефона
"""
import sys
from pathlib import Path

ROOT = Path(r"D:\Клод код\Инстаграм публикации")
SCR = Path(r"C:\Users\68664\AppData\Local\Temp\claude"
           r"\d-------------------------------"
           r"\275d5457-9faa-489f-8cb7-dd4be7d200dc\scratchpad")
sys.path.insert(0, str(ROOT / "src"))

import fullgen as F
import generate as gen
import build_day as B
from render_html import shot, data_uri

OUT = ROOT / "out" / "post_tyzhnia"
REAL = ROOT / "out" / "real" / "all"
FOUR = [REAL / "cord_ext.jpg", REAL / "maca_ext.jpg",
        REAL / "tribulus_ext.jpg", REAL / "ginseng_ext.jpg"]
CARD = SCR / "card_week.png"

INK = "#2f3128"
FOREST = "#2f4a2c"
FLAME = "#c0391b"          # колір плашки знижки на сайті

PATTERN = ("plain off-white paper background (RGB 246 245 238) with a faint "
           "outlined botanical pattern — thin pale beige line drawings of "
           "leaves and roots, barely visible. ")
TAIL = (" Soft natural shadows, clean catalogue look. NO TEXT anywhere in the "
        "image except wording printed on the product packaging. No stamps, "
        "seals or badges anywhere in the background.")
KEEP = (" Each jar keeps its own printed label exactly as in its photo. They "
        "are opaque WHITE bottles with dark labels. Draw no other small print.")
ONE = (" The jar keeps its own printed label exactly as in the attached photo. "
       "Draw no other small print on it.")

SCENES = {
    "1_обкладинка": (
        "Editorial product photograph: EXACTLY FOUR jars — the four from the "
        "attached photos — stand side by side in a neat row on soft green "
        "forest moss in the LOWER HALF of the frame, seen straight on, in warm "
        "low morning light with a blurred forest behind them. Nothing else in "
        "the frame. The TOP HALF is calm blurred forest and pale sky, almost "
        "empty." + TAIL + KEEP, FOUR),

    "2_що-в-добірці": (
        PATTERN + "The four jars from the attached photos stand in a neat row "
        "along the very BOTTOM EDGE of the frame, small, seen straight on, "
        "cropped by the bottom. The WHOLE UPPER TWO THIRDS is bare patterned "
        "paper, completely empty." + TAIL + KEEP, FOUR),

    "3_кордицепс": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "RIGHT corner, seen straight on, partly cropped by the bottom edge, "
        "with a few slender orange cordyceps militaris fruiting bodies lying at "
        "its base. The whole LEFT SIDE and the TOP are bare patterned paper, "
        "completely empty." + TAIL + ONE, [REAL / "cord_ext.jpg"]),

    "4_женьшень": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands on the RIGHT "
        "side, seen straight on, and beside its base lies a dried ginseng root "
        "and an empty espresso cup turned on its side. Everything stays "
        "strictly right of the vertical centre line. The LEFT HALF is bare "
        "patterned paper, completely empty." + TAIL + ONE,
        [REAL / "ginseng_ext.jpg"]),

    "5_мака": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "RIGHT, seen straight on, with two whole maca roots — pale golden "
        "tubers — lying beside it. The whole LEFT SIDE and the TOP are bare "
        "patterned paper, completely empty." + TAIL + ONE,
        [REAL / "maca_ext.jpg"]),

    "6_трібулус": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands on the RIGHT "
        "side, seen straight on, with a few yellow Tribulus terrestris flowers "
        "and green spiny leaves at its base. Everything stays strictly right of "
        "the vertical centre line. The LEFT HALF is bare patterned paper, "
        "completely empty." + TAIL + ONE, [REAL / "tribulus_ext.jpg"]),

    "7_фінал": (
        PATTERN + "The four jars from the attached photos stand in a neat row "
        "in the LOWER LEFT, SMALL, taking up no more than the bottom third of "
        "the frame height, seen straight on, with a wide soft watercolour blot "
        "behind them in deep forest green. They must NOT reach above the "
        "halfway line. The RIGHT HALF and the WHOLE UPPER HALF are bare "
        "patterned paper, completely empty." + TAIL + KEEP, FOUR),
}

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")


def base(bg, dark=False):
    fg = "#f6f2e6" if dark else INK
    return """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:Montserrat;overflow:hidden;
 position:relative;color:%s;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('%s') center/cover}
.cnt{position:absolute;top:4.4%%;left:6.4%%;right:6.4%%;display:flex;
 align-items:center;gap:12px;font-weight:600;font-size:19px;
 letter-spacing:.24em;text-transform:uppercase;color:%s;z-index:5}
.cnt i{flex:1;height:1px;background:%s;opacity:.45}
h1{font-weight:800;text-transform:uppercase;letter-spacing:-1.4px;line-height:.94}
h2{font-weight:700;text-transform:uppercase;letter-spacing:-.3px;line-height:1.06}
p{font-weight:400;line-height:1.38}
.rule{height:5px;margin:24px 0 22px}
""" % (fg, data_uri(bg), fg, fg)


def counter(n):
    return ("<div class='cnt'><span>Товар тижня</span><i></i>"
            "<span>%d / 7</span></div>" % n)


def page(css, body):
    css = css.replace("@F@", FOREST).replace("@C@", FLAME)
    return ("<html><head>%s<style>%s</style></head><body>"
            "<div class='bg'></div>%s</body></html>" % (FONTS, css, body))


def build(tag, bg):
    n = int(tag[0])

    if tag.startswith("1"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(14,24,12,.86) 0%,rgba(14,24,12,.4) 30%,rgba(14,24,12,0) 50%)}
.col{position:absolute;left:6.4%;right:6.4%;top:9%;text-align:center}
h1{font-size:96px}
h2{font-size:34px;font-weight:600;margin-top:16px;letter-spacing:.08em}
.off{display:inline-block;margin-top:26px;background:@C@;color:#fff;
 font-weight:800;font-size:56px;letter-spacing:-1px;padding:12px 34px;
 border-radius:14px}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Енергія<br>і тонус</h1>"
                "<h2>Чотири адаптогени · 14–20 вересня</h2>"
                "<div class='off'>−20%</div></div>")

    elif tag.startswith("2"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;right:6.4%;top:8%}
h1{font-size:70px;color:@F@}
.rule{width:150px;background:@C@}
.r{display:flex;align-items:baseline;justify-content:space-between;
 padding:17px 0;border-bottom:1px solid rgba(47,74,44,.18)}
.r b{font-weight:700;font-size:36px;letter-spacing:-.3px}
.r span{font-weight:800;font-size:40px;color:@C@;white-space:nowrap}
.r s{font-weight:500;font-size:29px;color:#8b8f80;margin-left:12px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Що в добірці</h1><div class='rule'></div>"
                "<div class='r'><b>Кордицепс, екстракт 10:1</b>"
                "<span>800 ₴<s>1000</s></span></div>"
                "<div class='r'><b>Мака перуанська, 10:1</b>"
                "<span>448 ₴<s>560</s></span></div>"
                "<div class='r'><b>Трібулус, екстракт</b>"
                "<span>512 ₴<s>640</s></span></div>"
                "<div class='r'><b>Женьшень, екстракт 10:1</b>"
                "<span>432 ₴<s>540</s></span></div></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:58%}
h1{font-size:76px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Кордицепс</h1><div class='rule'></div>"
                "<p>Перша година дня перестає йти на розігрів: не чекаєш, "
                "поки друга кава нарешті ввімкне. Екстракт 10:1, "
                "стандартизований на 50% полісахаридів.</p></div>")

    elif tag.startswith("4"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:56%}
h1{font-size:76px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Женьшень</h1><div class='rule'></div>"
                "<p>Тримає рівно й не дає провалу через годину — на відміну "
                "від третьої чашки. До вечора вдома ще лишається сила.</p>"
                "</div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:56%}
h1{font-size:76px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Мака<br>перуанська</h1>"
                "<div class='rule'></div>"
                "<p>Росте в Андах на висоті чотирьох кілометрів. Макаміди — "
                "речовина, якої більше немає ніде в природі.</p></div>")

    elif tag.startswith("6"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:56%}
h1{font-size:76px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Трібулус</h1><div class='rule'></div>"
                "<p>Наступний день після залу дається легше: за відновлення "
                "тут відповідає фракція стероїдних сапонінів якірців.</p>"
                "</div>")

    else:
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:46%}
h1{font-size:64px;color:@F@}
.rule{width:150px;background:@C@}
.row{font-weight:600;font-size:31px;color:#5c5f52;line-height:1.55}
.off{display:inline-block;margin-top:22px;background:@C@;color:#fff;
 font-weight:800;font-size:46px;letter-spacing:-1px;padding:10px 26px;
 border-radius:12px}
.phone{position:absolute;right:4%;bottom:5%;width:33%;
 border-radius:30px;overflow:hidden;border:8px solid #23241f;
 box-shadow:0 24px 56px rgba(20,22,16,.3)}
.phone img{display:block;width:100%}
"""
        body = ("<div class='col'><h1>Тиждень<br>на знижці</h1>"
                "<div class='rule'></div>"
                "<div class='row'>З 14 по 20 вересня<br>"
                "Чотири продукти в добірці<br>Фасовки 60 і 120 капсул</div>"
                "<div class='off'>−20%</div></div>"
                "<div class='phone'><img src='" + data_uri(CARD) + "'></div>")
    return page(css, body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_blank").mkdir(exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()
    for tag, (scene, refs) in SCENES.items():
        bg = OUT / ("bg_" + tag + ".png")
        if not bg.exists() and tok:
            prompt = scene + " " + " ".join(B.REF_MANY.split())
            ok = F.draw_ref(prompt, refs, tok, bg, aspect="4:5")
            print(("  ✔ фон " if ok else "  ✖ фон ") + tag, flush=True)
        if bg.exists():
            html = build(tag, bg)
            shot(html, OUT / (tag + ".png"))
            shot(html.replace("</style>",
                              ".col,.col *,.cnt{color:transparent!important}"
                              "</style>"),
                 OUT / "_blank" / (tag + ".png"))
            print("  ✔ кадр", tag, flush=True)
    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
