# -*- coding: utf-8 -*-
"""Карусель курсу «Стійкий спокій»: ашваганда і магній гліцинат.

Другий пост підряд про курс із двох банок, тому прийоми з
content/post_patterns.md беруться ІНШІ, ніж у «Щоденній основі» — інакше
стрічка виглядатиме як два однакові пости:

  1 обкладинка   вечірній кадр без продукту, ритм коротких фраз-крапок
  2 кадр болю    ніч, телефон у темряві; без продукту, список ознак
  3 ашваганда    одна буквальна метафора: корінь поруч із банкою
  4 магній       таблиця без таблиці: назви вгорі, числа внизу
  5 коли пити    два стовпці — ранок і вечір, форма вживання
  6 заперечення  найгучніший блок кадру: «це не снодійне»
  7 фінал        мокап телефона зі скріншотом НАШОЇ картки (909 грн)

Сьомий кадр — прийом, якого в попередній каруселі не було: ціну показує
не намальована плашка, а справжня сторінка з кнопкою «Купити».
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

OUT = ROOT / "out" / "post_spokij"
ASHWA = [ROOT / "out" / "real" / "all" / "ashwa_caps.jpg"]
MAG = [ROOT / "out" / "real" / "all" / "magnium.jpg"]
BOTH = [ROOT / "out" / "real" / "all" / "ashwa_caps.jpg",
        ROOT / "out" / "real" / "all" / "magnium.jpg"]
CARD = SCR / "card.png"

INK = "#2f3128"
OLIVE = "#7b812b"
PLUM = "#6b3a6e"          # колір етикетки ашваганди
NAVY = "#2b3a5c"          # колір етикетки магнію

PATTERN = ("plain off-white paper background (RGB 246 245 238) with a faint "
           "outlined botanical pattern — thin pale beige line drawings of "
           "leaves and roots, barely visible. ")
TAIL = (" Soft natural shadows, clean catalogue look, no dark corners. NO TEXT "
        "anywhere in the image except wording printed on the product packaging.")
LABEL = (" The jars keep their own printed labels: ЛІСОВИК, АШВАГАНДА, "
         "МАГНІЙ ГЛІЦИНАТ. Draw no other small print on them.")

SCENES = {
    "1_обкладинка": (
        "Quiet editorial photograph, no product and no packaging at all: a dark "
        "room in the late evening, a window with rain streaks, one warm lamp "
        "glowing low on the right, an armchair in shadow. Calm, still, almost "
        "silent. The LEFT HALF stays dark and empty for text." + TAIL, None),

    "2_вночі": (
        "Editorial photograph, no product and no packaging at all: a rumpled bed "
        "at night seen from above, an empty pillow, a phone lying face up on the "
        "sheet glowing cold blue in the dark, the rest of the frame almost "
        "black. Nobody in the frame. The TOP HALF stays dark and empty for "
        "text." + TAIL, None),

    "3_ашваганда": (
        PATTERN + "Behind the product a soft watercolour blot in muted plum "
        "purple. EXACTLY ONE jar — the ashwagandha jar from the attached photo — "
        "stands on the RIGHT. There is only one jar in the entire frame: no "
        "second jar, no duplicate, no reflection of another jar. Beside it, "
        "large and sharp, a few dried ashwagandha roots — "
        "pale woody roots with fine fibres. Everything stays STRICTLY right of "
        "the vertical centre line. The LEFT HALF is bare patterned paper."
        + TAIL + LABEL, ASHWA),

    "4_магній": (
        PATTERN + "The magnesium jar from the attached photo stands exactly in "
        "the CENTRE of the frame, alone, seen straight on, with a few grey "
        "mineral crystals at its base and a soft navy watercolour blot behind "
        "it. The TOP QUARTER and the BOTTOM QUARTER of the frame are bare "
        "patterned paper, completely empty." + TAIL + LABEL, MAG),

    "5_коли-пити": (
        PATTERN + "Two small still lifes side by side on the same paper, "
        "divided by nothing: on the LEFT a morning glass of water with soft "
        "daylight, on the RIGHT a warm ceramic cup of herbal tea with a small "
        "lit candle and evening lamp light. Two capsules lie beside each. The "
        "products are NOT in this frame. The TOP THIRD is bare patterned "
        "paper." + TAIL, None),

    "6_не-снодійне": (
        "Quiet dark editorial photograph, no product and no packaging: a bedside "
        "table at night with a switched-off lamp, a folded book and a glass of "
        "water, deep shadows, one faint warm highlight. Nothing else. The TOP "
        "HALF stays dark and empty for text." + TAIL, None),

    "7_фінал": (
        PATTERN + "Both jars from the attached photos stand together in the "
        "LOWER LEFT part of the frame, seen straight on, with a wide soft "
        "watercolour blot behind them — plum purple blending into navy. A few "
        "grey crystals and dried roots lie at their base. The RIGHT HALF and "
        "the TOP THIRD are bare patterned paper, completely empty."
        + TAIL + LABEL, BOTH),
}

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")


def base(bg, dark=False):
    fg = "#f4f1e8" if dark else INK
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
ul{list-style:none}
li{font-weight:500;line-height:1.32;margin-bottom:16px;padding-left:26px;
 position:relative}
li:before{content:'';position:absolute;left:0;top:.52em;width:10px;height:10px;
 border-radius:50%%;background:currentColor;opacity:.8}
""" % (fg, data_uri(bg), fg, fg)


def counter(n):
    return ("<div class='cnt'><span>Стійкий спокій</span><i></i>"
            "<span>%d / 7</span></div>" % n)


def page(css, body):
    return ("<html><head>%s<style>%s</style></head><body>"
            "<div class='bg'></div>%s</body></html>" % (FONTS, css, body))


def build(tag, bg):
    n = int(tag[0])

    if tag.startswith("1"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(96deg,
 rgba(8,10,14,.92) 0%,rgba(8,10,14,.78) 34%,rgba(8,10,14,.4) 58%,
 rgba(8,10,14,0) 82%)}
.col{position:absolute;left:6.4%;top:16%;width:52%}
h1{font-size:88px}
p{font-size:36px;margin-top:26px;opacity:.9;line-height:1.5}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Стійкий<br>спокій</h1>"
                "<p>Не швидше.<br>Не голосніше.<br>Просто рівно.</p></div>")

    elif tag.startswith("2"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(6,8,12,.92) 0%,rgba(6,8,12,.8) 38%,rgba(6,8,12,.34) 60%,
 rgba(6,8,12,0) 80%)}
.col{position:absolute;left:6.4%;top:13%;width:56%}
h1{font-size:62px}
.rule{width:140px;background:#f4f1e8;opacity:.55}
li{font-size:30px}
p{font-size:26px;opacity:.75;margin-top:10px;font-style:italic}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Тіло лягло,<br>голова ні</h1>"
                "<div class='rule'></div><ul>"
                "<li>Думки ганяють по колу</li>"
                "<li>Прокидаєшся серед ночі</li>"
                "<li>Дрібниці чіпляють сильніше, ніж мали б</li>"
                "</ul><p>Знайомий вечір.</p></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:18%;width:40%}
h1{font-size:76px;color:#6b3a6e}h2{font-size:30px;margin-top:12px}
.rule{width:150px;background:#6b3a6e}
p{font-size:31px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Ашваганда</h1>"
                "<h2>екстракт кореня</h2><div class='rule'></div>"
                "<p>Корінь, який в аюрведі вживали тисячоліттями. "
                "У капсулі — концентрований екстракт, не мелений порошок.</p>"
                "</div>")

    elif tag.startswith("4"):
        # таблиця без таблиці: назви вгорі, числа внизу, товар посередині
        css = base(bg) + """
.top{position:absolute;left:8%;right:8%;top:12%;text-align:center}
h1{font-size:66px;color:#2b3a5c}
.sub{font-weight:600;font-size:26px;letter-spacing:.2em;text-transform:uppercase;
 color:#5c5f52;margin-top:14px}
.bot{position:absolute;left:8%;right:8%;bottom:9%;display:flex;
 justify-content:space-between;text-align:center}
.b{flex:1}
.b b{display:block;font-weight:800;font-size:44px;color:#2b3a5c;
 letter-spacing:-1px}
.b span{display:block;font-weight:500;font-size:23px;color:#5c5f52;margin-top:6px}
.b+.b{border-left:1px solid rgba(43,58,92,.22)}
"""
        body = (counter(n) +
                "<div class='top'><h1>Магній<br>гліцинат</h1>"
                "<div class='sub'>форма, яку переносять мʼякше</div></div>"
                "<div class='bot'>"
                "<div class='b'><b>208 мг</b><span>магнію в добовій дозі</span></div>"
                "<div class='b'><b>55%</b><span>референсної норми</span></div>"
                "<div class='b'><b>60</b><span>капсул у банці</span></div>"
                "</div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.top{position:absolute;left:8%;right:8%;top:9%;text-align:center}
h1{font-size:64px}
.rule{width:140px;background:#7b812b;margin:20px auto 0}
.two{position:absolute;left:8%;right:8%;top:30%;display:flex;gap:40px}
.c{flex:1;text-align:center}
.c em{display:block;font-style:normal;font-weight:600;font-size:22px;
 letter-spacing:.24em;text-transform:uppercase;color:#7b812b}
.c b{display:block;font-weight:800;font-size:40px;margin-top:12px;
 letter-spacing:-.5px}
.c span{display:block;font-weight:500;font-size:25px;color:#5c5f52;margin-top:8px}
"""
        body = (counter(n) +
                "<div class='top'><h1>Двічі на день</h1>"
                "<div class='rule'></div></div>"
                "<div class='two'>"
                "<div class='c'><em>Зранку</em><b>1 + 1</b>"
                "<span>ашваганда за 15 хвилин до їжі, магній поруч</span></div>"
                "<div class='c'><em>Увечері</em><b>1 + 1</b>"
                "<span>та сама пара, ближче до вечері</span></div>"
                "</div>")

    elif tag.startswith("6"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(6,8,12,.93) 0%,rgba(6,8,12,.72) 42%,rgba(6,8,12,.2) 66%,
 rgba(6,8,12,0) 84%)}
.col{position:absolute;left:6.4%;right:10%;top:14%}
h1{font-size:78px}
.rule{width:150px;background:#f4f1e8;opacity:.55}
p{font-size:31px;opacity:.9;max-width:86%}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Це не<br>снодійне</h1>"
                "<div class='rule'></div>"
                "<p>Курс не вимикає ввечері й не тримає зранку. "
                "Ашваганда — рослина, магній — мінерал; обидва працюють "
                "накопичувально, а не з першої капсули.</p></div>")

    else:
        # фінал: мокап телефона зі скріншотом нашої ж картки
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:12%;width:52%;text-align:left}
h1{font-size:62px}
.rule{width:140px;background:#7b812b}
.row{font-weight:600;font-size:25px;color:#5c5f52;line-height:1.7}
.phone{position:absolute;right:5%;bottom:6%;width:39%;
 border-radius:34px;overflow:hidden;border:9px solid #23241f;
 box-shadow:0 26px 60px rgba(20,22,16,.3)}
.phone img{display:block;width:100%}
"""
        body = (counter(n) +
                "<div class='col'><h1>Курс на<br>місяць</h1>"
                "<div class='rule'></div>"
                "<div class='row'>дві банки · 120 капсул<br>"
                "по дві на добу · 30 днів</div></div>"
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
                              ".col,.top,.bot,.two,.phone{visibility:hidden}</style>"),
                 OUT / "_blank" / (tag + ".png"))
            print("  ✔ кадр", tag, flush=True)
    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
