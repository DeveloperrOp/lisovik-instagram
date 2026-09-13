# -*- coding: utf-8 -*-
"""Карусель: Омега-3 риб'ячий жир, капсули 1 г.

Головна думка картки — не про користь узагалі, а про те, ЯК читати
етикетку: «1000 мг риб'ячого жиру» це маса олії в капсулі, а не
кількість EPA і DHA. Заради цих двох кислот жир і беруть, і саме їх
треба порівнювати між банками. На цьому й побудована карусель.

🚨 Правило власника: ПРОДУКТ НА ПЕРШОМУ КАДРІ. Обкладинка зроблена тим
самим прийомом, що спрацював на трібулусі, — «килим сировини в колір
етикетки»: бурштинові капсули риб'ячого жиру на весь кадр збігаються
з мідно-помаранчевою етикеткою, і продукт видно з першої секунди.

  1 обкладинка   килим бурштинових капсул, банка по центру
  2 не те число  «1000 мг» — маса олії, а не омега
  3 два числа    EPA 184 і DHA 124 в капсулі
  4 616          добова сума проти порога 250 мг
  5 льон         лляна олія — це ALA, інша кислота
  6 що дає       серце, суглоби, шкіра взимку, відновлення
  7 фінал        дві фасовки й мокап телефона з карткою
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

OUT = ROOT / "out" / "post_omega"
JAR = [ROOT / "out" / "real" / "all" / "omega.jpg"]
CARD = SCR / "card_omega.png"

INK = "#2f3128"
FOREST = "#2f4a2c"
COPPER = "#c1552a"        # мідно-помаранчевий з етикетки

PATTERN = ("plain off-white paper background (RGB 246 245 238) with a faint "
           "outlined botanical pattern — thin pale beige line drawings of "
           "leaves and roots, barely visible. ")
TAIL = (" Soft natural shadows, clean catalogue look. NO TEXT anywhere in the "
        "image except wording printed on the product packaging. No stamps, "
        "seals or badges anywhere in the background.")
LABEL = (" The jar keeps its own printed label exactly as in the photo: "
         "ЛІСОВИК, ОМЕГА-3 РИБ'ЯЧИЙ ЖИР. It is an opaque WHITE bottle with a "
         "warm copper-orange label. Draw no other small print on it.")
SOFTGEL = ("amber translucent oval fish-oil softgel capsules, glossy, the "
           "golden oil clearly visible through the shell")

SCENES = {
    "1_обкладинка": (
        "Editorial product photograph seen straight down: the whole frame is a "
        "dense carpet of " + SOFTGEL + ", edge to edge, no gaps, shot from "
        "above in bright even daylight, warm amber tones filling everything. "
        "EXACTLY ONE jar — the one from the attached photo — lies in the CENTRE "
        "on top of the capsules, slightly turned, large and sharp. The TOP "
        "QUARTER of the frame is calm capsules only, no jar there."
        + TAIL + LABEL, JAR),

    "2_не-те-число": (
        PATTERN + "Macro photograph: a single " + SOFTGEL[:-1] + " lies alone "
        "in the LOWER RIGHT of the frame, enormous and razor sharp, a soft "
        "highlight running along its edge. No product, no packaging, no jar. "
        "The WHOLE LEFT SIDE and the TOP are bare patterned paper, completely "
        "empty." + TAIL, None),

    "3_два-числа": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "RIGHT corner, seen straight on, partly cropped by the bottom edge, "
        "with three " + SOFTGEL + " lying at its base. The whole LEFT SIDE and "
        "the TOP of the frame are bare patterned paper, completely empty."
        + TAIL + LABEL, JAR),

    "4_шістсот": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands on the RIGHT "
        "side, seen straight on, and beside its base lie a few " + SOFTGEL +
        ". Everything stays strictly right of the vertical centre line. The "
        "LEFT HALF is bare patterned paper, completely empty." + TAIL + LABEL,
        JAR),

    "5_льон": (
        PATTERN + "Still life in the LOWER THIRD of the frame: a small glass "
        "bowl of golden flaxseed oil with a scatter of brown flax seeds beside "
        "it, and separately, clearly apart, two " + SOFTGEL + ". No product, "
        "no packaging, no jar. The UPPER TWO THIRDS are bare patterned paper, "
        "completely empty." + TAIL, None),

    "6_що-дає": (
        PATTERN + "A tall glass of water stands on the paper in the morning "
        "light, and in front of it two " + SOFTGEL + " lie side by side on a "
        "linen napkin. The jar from the attached photo stands behind, slightly "
        "out of focus and CROPPED by the right edge of the frame. The TOP HALF "
        "is bare patterned paper, completely empty." + TAIL + LABEL, JAR),

    "7_фінал": (
        PATTERN + "EXACTLY ONE jar from the attached photo stands in the LOWER "
        "LEFT CORNER, SMALL, taking up no more than the bottom third of the "
        "frame height, seen straight on, with a soft watercolour blot behind "
        "it in warm copper orange, and a few "
        + SOFTGEL + " at its base. The jar must NOT reach above the halfway "
        "line. The RIGHT HALF and the WHOLE UPPER HALF are bare patterned "
        "paper, completely empty." + TAIL + LABEL, JAR),
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
    return ("<div class='cnt'><span>Омега-3</span><i></i>"
            "<span>%d / 7</span></div>" % n)


def page(css, body):
    css = css.replace("@F@", FOREST).replace("@C@", COPPER)
    return ("<html><head>%s<style>%s</style></head><body>"
            "<div class='bg'></div>%s</body></html>" % (FONTS, css, body))


def build(tag, bg):
    n = int(tag[0])

    if tag.startswith("1"):
        css = base(bg, dark=True) + """
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(60,22,8,.84) 0%,rgba(60,22,8,.36) 28%,rgba(60,22,8,0) 48%,
 rgba(60,22,8,.42) 84%,rgba(60,22,8,.68) 100%)}
.col{position:absolute;left:6.4%;right:6.4%;top:10%;text-align:center}
h1{font-size:120px}
h2{font-size:36px;font-weight:600;margin-top:18px;letter-spacing:.08em}
"""
        body = ("<div class='sh'></div>" + counter(n) +
                "<div class='col'><h1>Омега-3</h1>"
                "<h2>EPA 368 + DHA 248 мг на добу</h2></div>")

    elif tag.startswith("2"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:10%;width:58%}
h1{font-size:78px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:38px}
"""
        body = (counter(n) +
                "<div class='col'><h1>1000 мг —<br>це не<br>омега</h1>"
                "<div class='rule'></div>"
                "<p>Так виглядає найпоширеніша плутанина на полиці. "
                "Це маса олії в капсулі, а не кількість самих кислот — "
                "заради яких риб'ячий жир і беруть.</p></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:60%}
h1{font-size:72px;color:@F@}
.rule{width:150px;background:@C@}
.f{margin-bottom:26px}
.f b{display:block;font-weight:800;font-size:46px;letter-spacing:-.6px}
.f span{display:block;font-weight:500;font-size:31px;color:#5c5f52;margin-top:4px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Два числа,<br>які варто<br>читати</h1>"
                "<div class='rule'></div>"
                "<div class='f'><b>EPA 184 мг</b>"
                "<span>у кожній капсулі</span></div>"
                "<div class='f'><b>DHA 124 мг</b>"
                "<span>у кожній капсулі</span></div>"
                "<div class='f'><b>Обидва — на етикетці</b>"
                "<span>прямим текстом, а не дрібним шрифтом</span></div></div>")

    elif tag.startswith("4"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:12%;width:48%}
.big{font-weight:800;font-size:190px;color:@F@;line-height:.82;
 letter-spacing:-9px}
h2{font-size:40px;margin-top:14px}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><div class='big'>616</div>"
                "<h2>мг на добу</h2><div class='rule'></div>"
                "<p>Офіційне формулювання про серце дозволене від 250 мг "
                "EPA і DHA. Тут виходить у два з половиною раза більше.</p>"
                "</div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:10%;width:60%}
h1{font-size:74px;color:@F@}
.rule{width:150px;background:@C@}
p{font-size:37px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Лляна олія —<br>інша омега</h1>"
                "<div class='rule'></div>"
                "<p>У ній ALA, а не EPA і DHA. Одна родина, різні кислоти, "
                "і замінити одну одною не вийде. Тому на банці стоять "
                "саме ті дві.</p></div>")

    elif tag.startswith("6"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:9%;width:58%}
h1{font-size:72px;color:@F@}
.rule{width:150px;background:@C@}
.f{margin-bottom:22px}
.f b{display:block;font-weight:800;font-size:40px;letter-spacing:-.4px}
.f span{display:block;font-weight:500;font-size:30px;color:#5c5f52;margin-top:3px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Що дає<br>курс</h1>"
                "<div class='rule'></div>"
                "<div class='f'><b>Робота серця</b>"
                "<span>EPA і DHA сприяють нормальній роботі серця</span></div>"
                "<div class='f'><b>Суглоби в русі</b>"
                "<span>причина, з якої омегу беруть роками без перерв</span></div>"
                "<div class='f'><b>Шкіра взимку</b>"
                "<span>опалення й сухе повітря — сезон жирних кислот</span></div>"
                "<div class='f'><b>Легше відновлення</b>"
                "<span>після важкого тижня тіло приходить до норми спокійніше</span>"
                "</div></div>")

    else:
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:10%;width:44%}
h1{font-size:66px;color:@F@}
.rule{width:150px;background:@C@}
.row{font-weight:600;font-size:30px;color:#5c5f52;line-height:1.55}
.phone{position:absolute;right:4%;bottom:5%;width:33%;
 border-radius:30px;overflow:hidden;border:8px solid #23241f;
 box-shadow:0 24px 56px rgba(20,22,16,.3)}
.phone img{display:block;width:100%}
"""
        body = (counter(n) +
                "<div class='col'><h1>Дві<br>фасовки</h1><div class='rule'></div>"
                "<div class='row'>100 капсул — 50 днів, 14 ₴ на день<br>"
                "60 капсул — 30 днів, 15 ₴ на день<br>"
                "добова доза в обох однакова</div></div>"
                "<div class='phone'><img src='%s'></div>" % data_uri(CARD))
    return page(css, body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_blank").mkdir(exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()
    for tag, (scene, refs) in SCENES.items():
        bg = OUT / ("bg_" + tag + ".png")
        if not bg.exists() and tok:
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
                              ".col,.col *,.cnt{color:transparent!important}"
                              "</style>"),
                 OUT / "_blank" / (tag + ".png"))
            print("  ✔ кадр", tag, flush=True)
    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
