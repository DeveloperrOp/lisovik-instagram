# -*- coding: utf-8 -*-
"""Карусель: Трібулус, екстракт 10:1, капсули 120 шт.

Це не курс, а один товар — тому розмова інша: не «дві банки разом», а що
всередині однієї і чим екстракт відрізняється від меленої трави.

🚨 Нове правило власника (11.09.2026): ПРОДУКТ НА ПЕРШОМУ КАДРІ.
Обкладинка тут зроблена прийомом «килим сировини в колір етикетки»:
жовті квіти якірців на весь фон, банка по центру — фон збігається з
етикеткою, і продукт видно з першої секунди.

  1 обкладинка   килим квітів якірців, банка по центру
  2 що це        рослина крупно: колючий плід і квітка
  3 екстракт     гігантська цифра 10:1
  4 сапоніни     таблиця без таблиці: 90% і що це означає
  5 як приймати  форма вживання: дві капсули і склянка води
  6 на скільки   120 капсул — 60 днів
  7 фінал        мокап телефона зі скріншотом картки (640 грн)
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

OUT = ROOT / "out" / "post_tribulus"
JAR = [ROOT / "out" / "real" / "all" / "tribulus_ext.jpg"]
CARD = SCR / "card_trib.png"

INK = "#2f3128"
FOREST = "#2f4a2c"        # темно-зелений з етикетки
GOLD = "#c8951f"          # жовтий квітів якірців

PATTERN = ("plain off-white paper background (RGB 246 245 238) with a faint "
           "outlined botanical pattern — thin pale beige line drawings of "
           "leaves and roots, barely visible. ")
TAIL = (" Soft natural shadows, clean catalogue look. NO TEXT anywhere in the "
        "image except wording printed on the product packaging.")
LABEL = (" The jar keeps its own printed label exactly as in the photo: "
         "ЛІСОВИК, ТРІБУЛУС, and the small round badge ЕКСТРАКТ 10:1. It is an "
         "opaque WHITE bottle with a deep forest-green label covered in small "
         "yellow flowers. Draw no other small print on it.")

SCENES = {
    "1_обкладинка": (
        "Editorial product photograph seen straight down: the whole frame is a "
        "dense carpet of fresh yellow Tribulus terrestris flowers and green "
        "spiny leaves, edge to edge, no gaps, shot from above in bright even "
        "daylight. EXACTLY ONE jar — the one from the attached photo — lies in "
        "the CENTRE on top of the flowers, slightly turned, large and sharp. "
        "The TOP QUARTER of the frame is calm flowers only, no jar there."
        + TAIL + LABEL, JAR),

    "2_що-це": (
        PATTERN + "Macro photograph: a single dried spiny Tribulus fruit — a "
        "small woody star with sharp thorns — and one yellow flower with five "
        "petals, lying together on the paper, very large and sharp, side by "
        "side. No product, no packaging, no jar in this frame. The TOP HALF is "
        "bare patterned paper, completely empty." + TAIL, None),

    "3_екстракт": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands on the RIGHT "
        "side of the frame, seen straight on. Beside its base lies a small neat "
        "heap of dried crushed green herb, and next to that a single capsule. "
        "Everything stays strictly right of the vertical centre line. The LEFT "
        "HALF is bare patterned paper, completely empty." + TAIL + LABEL, JAR),

    "4_сапоніни": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands exactly in "
        "the CENTRE of the frame, alone, seen straight on, SMALLER than usual so "
        "that it occupies only the middle third of the height, with three "
        "yellow Tribulus flowers lying at its base. The TOP THIRD and the "
        "BOTTOM THIRD of the frame are bare patterned paper, completely "
        "empty — the jar and its shadow must not reach into them." + TAIL + LABEL, JAR),

    "5_як-приймати": (
        PATTERN + "A tall glass of water stands on the paper in the morning "
        "light, and in front of it two capsules lie side by side on a linen "
        "napkin. The jar from the attached photo stands behind, slightly out of "
        "focus and CROPPED by the right edge of the frame. The TOP HALF is bare "
        "patterned paper, completely empty." + TAIL + LABEL, JAR),

    "6_на-скільки": (
        PATTERN + "Seen straight down: many small identical CAPSULES — plain "
        "beige gelatin capsules, each about the size of a bean — laid out on "
        "the paper in neat even rows like a calendar grid, filling the RIGHT "
        "HALF of the frame. EXACTLY ONE jar from the attached photo lies on "
        "its side in the BOTTOM RIGHT corner, partly cropped by the edge. "
        "There is only ONE jar in the whole frame — no second bottle, no "
        "duplicates, no rows of bottles. The LEFT HALF is bare patterned "
        "paper, completely empty." + TAIL + LABEL, JAR),

    "7_фінал": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "LEFT CORNER, fully inside the left half, seen straight on, with a wide "
        "soft watercolour blot behind it in deep forest green, and a few yellow "
        "Tribulus flowers at its base. The RIGHT HALF and the TOP THIRD are "
        "bare patterned paper, completely empty." + TAIL + LABEL, JAR),
}

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")


def base(bg, dark=False):
    fg = "#f6f2e6" if dark else INK
    return """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;font-family:Montserrat;overflow:hidden;
 position:relative;color:%s}
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
    return ("<div class='cnt'><span>Трібулус</span><i></i>"
            "<span>%d / 7</span></div>" % n)


def page(css, body):
    return ("<html><head>%s<style>%s</style></head><body>"
            "<div class='bg'></div>%s</body></html>" % (FONTS, css, body))


def build(tag, bg):
    n = int(tag[0])

    if tag.startswith("1"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(18,28,14,.78) 0%,rgba(18,28,14,.32) 26%,rgba(18,28,14,0) 46%,
 rgba(18,28,14,.35) 84%,rgba(18,28,14,.6) 100%)}
.col{position:absolute;left:6.4%;right:6.4%;top:11%;text-align:center}
h1{font-size:104px}
h2{font-size:36px;font-weight:600;margin-top:18px;letter-spacing:.22em}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Трібулус</h1>"
                "<h2>екстракт 10:1</h2></div>")

    elif tag.startswith("2"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:11%;width:52%}
h1{font-size:78px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
p{font-size:40px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Якірці<br>сланкі</h1>"
                "<div class='rule'></div>"
                "<p>Колюча трава, що стелиться по сухій землі. У банці — тільки її екстракт і рослинна оболонка. Без желатину й наповнювачів: склад у один рядок.</p></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:15%;width:42%}
.big{font-weight:800;font-size:190px;color:#2f4a2c;line-height:.82;
 letter-spacing:-8px}
h2{font-size:46px;margin-top:16px}
.rule{width:150px;background:#c8951f}
p{font-size:40px}
"""
        body = (counter(n) +
                "<div class='col'><div class='big'>10:1</div>"
                "<h2>десять до одного</h2><div class='rule'></div>"
                "<p>Стільки трави випарюють, щоб лишилась одна частина. У капсулі концентрат, а не мелений бурʼян.</p></div>")

    elif tag.startswith("4"):
        css = base(bg) + """
.top{position:absolute;left:8%;right:8%;top:11%;text-align:center}
h1{font-size:74px;color:#2f4a2c}
.sub{font-weight:600;font-size:30px;letter-spacing:.2em;text-transform:uppercase;
 color:#5c5f52;margin-top:14px}
.bot{position:absolute;left:8%;right:8%;bottom:9%;display:flex;text-align:center}
.b{flex:1}
.b b{display:block;font-weight:800;font-size:58px;color:#2f4a2c;letter-spacing:-1px}
.b span{display:block;font-weight:500;font-size:28px;color:#5c5f52;margin-top:6px}
.b+.b{border-left:1px solid rgba(47,74,44,.2)}
"""
        body = (counter(n) +
                "<div class='top'><h1>Виміряно,<br>а не обіцяно</h1>"
                "<div class='sub'>у траві сапонінів то більше, то менше — в екстракті їх фіксують числом</div></div>"
                "<div class='bot'>"
                "<div class='b'><b>90%</b><span>сапонінів у екстракті</span></div>"
                "<div class='b'><b>1200 мг</b><span>екстракту на добу</span></div>"
                "<div class='b'><b>120</b><span>капсул у банці</span></div>"
                "</div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:12%;width:48%}
h1{font-size:78px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
.s{display:flex;align-items:flex-start;margin-bottom:24px}
.s em{flex:0 0 62px;height:62px;border:2px solid #2f4a2c;border-radius:50%;
 font-style:normal;font-weight:800;font-size:29px;color:#2f4a2c;
 display:flex;align-items:center;justify-content:center;margin-right:18px}
.s b{display:block;font-weight:800;font-size:40px;text-transform:uppercase;
 letter-spacing:-.3px}
.s span{display:block;font-weight:500;font-size:31px;color:#5c5f52;margin-top:3px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Як приймати</h1><div class='rule'></div>"
                "<div class='s'><em>2</em><div><b>Капсули</b>"
                "<span>один раз на день</span></div></div>"
                "<div class='s'><em>1</em><div><b>Склянка води</b>"
                "<span>повна, не пів</span></div></div>"
                "<div class='s'><em>∅</em><div><b>Без прив'язки</b>"
                "<span>до їжі та години</span></div></div></div>")

    elif tag.startswith("6"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:16%;width:40%}
.big{font-weight:800;font-size:200px;color:#2f4a2c;line-height:.82;
 letter-spacing:-10px}
h2{font-size:50px;margin-top:14px}
.rule{width:150px;background:#c8951f}
p{font-size:40px}
"""
        body = (counter(n) +
                "<div class='col'><div class='big'>60</div>"
                "<h2>днів з однієї<br>банки</h2><div class='rule'></div>"
                "<p>120 капсул, по дві на добу. Менша банка на 60 капсул "
                "закриває рівно місяць.</p></div>")

    else:
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:12%;width:50%}
h1{font-size:74px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
.row{font-weight:600;font-size:31px;color:#5c5f52;line-height:1.7}
.phone{position:absolute;right:4%;bottom:5%;width:33%;
 border-radius:30px;overflow:hidden;border:8px solid #23241f;
 box-shadow:0 24px 56px rgba(20,22,16,.3)}
.phone img{display:block;width:100%}
"""
        body = (counter(n) +
                "<div class='col'><h1>Дві фасовки</h1><div class='rule'></div>"
                "<div class='row'>120 капсул · 60 днів<br>"
                "60 капсул · 30 днів</div></div>"
                "<div class='phone'><img src='%s'></div>" % data_uri(CARD))
    return page(css, body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_blank").mkdir(exist_ok=True)
    tok = gen.token()
    for tag, (scene, refs) in SCENES.items():
        bg = OUT / ("bg_" + tag + ".png")
        if not bg.exists():
            prompt = scene
            if refs:
                prompt += " " + " ".join(B.REF_MANY.split())
                ok = F.draw_ref(prompt, refs, tok, bg, aspect="4:5")
            else:
                ok = F.draw_raw(prompt, tok, bg, aspect="4:5")
            print(("  ✔ фон " if ok else "  ✖ фон ") + tag, flush=True)
        if bg.exists():
            html = build(tag, bg)
            shot(html, OUT / (tag + ".png"))
            shot(html.replace("</style>",
                              ".col,.top,.bot,.phone{visibility:hidden}</style>"),
                 OUT / "_blank" / (tag + ".png"))
            print("  ✔ кадр", tag, flush=True)
    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
