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

    "2_біль": (
        "Editorial photograph, no product and no packaging at all: a man's gym "
        "bag dropped on a bench in a dim locker room in the evening, a towel "
        "and an empty water bottle beside it, nobody in the frame, tired quiet "
        "light. The TOP HALF stays dark and empty for text." + TAIL, None),

    "3_що-дає": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "RIGHT corner of the frame, seen straight on, partly cropped by the "
        "bottom edge, with two yellow Tribulus flowers at its base. The whole "
        "LEFT SIDE and the TOP of the frame are bare patterned paper, "
        "completely empty." + TAIL + LABEL, JAR),

    "4_дев-яносто": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands on the RIGHT "
        "side, seen straight on, and beside its base lies a small heap of dried "
        "crushed green herb. Everything stays strictly right of the vertical "
        "centre line. The LEFT HALF is bare patterned paper, completely empty."
        + TAIL + LABEL, JAR),

    "5_без-гормонів": (
        PATTERN + "Macro photograph: three yellow Tribulus flowers and a few "
        "green spiny leaves lying loosely on the paper in the LOWER THIRD of "
        "the frame, large and sharp. No product, no packaging, no jar. The "
        "UPPER TWO THIRDS are bare patterned paper, completely empty."
        + TAIL, None),

    "6_ціна-дня": (
        PATTERN + "A tall glass of water stands on the paper in the morning "
        "light, and in front of it two capsules lie side by side on a linen "
        "napkin. The jar from the attached photo stands behind, slightly out of "
        "focus and CROPPED by the right edge of the frame. The TOP HALF is bare "
        "patterned paper, completely empty." + TAIL + LABEL, JAR),

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
 rgba(18,28,14,.82) 0%,rgba(18,28,14,.34) 28%,rgba(18,28,14,0) 48%,
 rgba(18,28,14,.4) 84%,rgba(18,28,14,.66) 100%)}
.col{position:absolute;left:6.4%;right:6.4%;top:10%;text-align:center}
h1{font-size:104px}
h2{font-size:38px;font-weight:600;margin-top:18px;letter-spacing:.1em}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Трібулус</h1>"
                "<h2>90% сапонінів · 1200 мг на добу</h2></div>")

    elif tag.startswith("2"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(8,10,8,.93) 0%,rgba(8,10,8,.8) 40%,rgba(8,10,8,.3) 62%,
 rgba(8,10,8,0) 82%)}
.col{position:absolute;left:6.4%;top:11%;width:60%}
h1{font-size:70px}
.rule{width:150px;background:#c8951f}
p{font-size:38px;opacity:.94}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Тренування є,<br>а результату<br>наче й ні</h1>"
                "<div class='rule'></div>"
                "<p>Після залу решта дня викреслена. Зранку тіло важке. "
                "І щотижня все більше здається, що це вік, а не втома.</p></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:62%}
h1{font-size:72px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
.f{margin-bottom:24px}
.f b{display:block;font-weight:800;font-size:40px;letter-spacing:-.4px}
.f span{display:block;font-weight:500;font-size:31px;color:#5c5f52;margin-top:4px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Що дає<br>курс</h1><div class='rule'></div>"
                "<div class='f'><b>Легше тримати навантаження</b>"
                "<span>тренування перестає бути тим, після чого решта дня "
                "викреслена</span></div>"
                "<div class='f'><b>Швидше відновлення</b>"
                "<span>наступний день після залу дається легше</span></div>"
                "<div class='f'><b>Стабільний тонус удень</b>"
                "<span>енергія тримається рівно, без ям між прийомами їжі</span>"
                "</div></div>")

    elif tag.startswith("4"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:12%;width:46%}
.big{font-weight:800;font-size:180px;color:#2f4a2c;line-height:.82;
 letter-spacing:-8px}
h2{font-size:44px;margin-top:14px}
.rule{width:150px;background:#c8951f}
p{font-size:38px}
"""
        body = (counter(n) +
                "<div class='col'><div class='big'>90%</div>"
                "<h2>сапонінів</h2><div class='rule'></div>"
                "<p>Типовий екстракт на ринку — 40–60%. Цю цифру майже ніхто "
                "не дивиться, а саме вона й відрізняє банки одна від одної.</p>"
                "</div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:11%;width:60%}
h1{font-size:76px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
p{font-size:38px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Без<br>гормонів</h1>"
                "<div class='rule'></div>"
                "<p>Це рослинний екстракт, а не гормональний препарат. "
                "Дія накопичувальна: ефект збирається курсом на 4–8 тижнів.</p>"
                "</div>")

    elif tag.startswith("6"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:10%;width:52%}
h1{font-size:72px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
.s{display:flex;align-items:flex-start;margin-bottom:22px}
.s em{flex:0 0 62px;height:62px;border:2px solid #2f4a2c;border-radius:50%;
 font-style:normal;font-weight:800;font-size:29px;color:#2f4a2c;
 display:flex;align-items:center;justify-content:center;margin-right:18px}
.s b{display:block;font-weight:800;font-size:40px;letter-spacing:-.3px}
.s span{display:block;font-weight:500;font-size:31px;color:#5c5f52;margin-top:3px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Дві капсули<br>на день</h1>"
                "<div class='rule'></div>"
                "<div class='s'><em>1</em><div><b>Один прийом</b>"
                "<span>1200 мг екстракту, будь-коли</span></div></div>"
                "<div class='s'><em>60</em><div><b>Днів з банки</b>"
                "<span>120 капсул на два місяці</span></div></div>"
                "<div class='s'><em>₴</em><div><b>10,67 на день</b>"
                "<span>стільки коштує доба курсу</span></div></div></div>")

    else:
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:11%;width:50%}
h1{font-size:66px;color:#2f4a2c}
.rule{width:150px;background:#c8951f}
.row{font-weight:600;font-size:33px;color:#5c5f52;line-height:1.6}
.phone{position:absolute;right:4%;bottom:5%;width:33%;
 border-radius:30px;overflow:hidden;border:8px solid #23241f;
 box-shadow:0 24px 56px rgba(20,22,16,.3)}
.phone img{display:block;width:100%}
"""
        body = (counter(n) +
                "<div class='col'><h1>Дві<br>фасовки</h1><div class='rule'></div>"
                "<div class='row'>120 капсул — 60 днів<br>"
                "60 капсул — 30 днів<br>екстракт у них однаковий</div></div>"
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
