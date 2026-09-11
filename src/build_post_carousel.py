# -*- coding: utf-8 -*-
"""Карусель курсу «Щоденна основа», зібрана за каталогом наших прийомів.

content/post_patterns.md — 41 прийом, знятий зі 100 наших опублікованих
кадрів. Тут кожен кадр робиться СВОЇМ прийомом, а не сьомим повтором банки:

  1 обкладинка   фон = інфографіка: крапля олії в холодній воді. Продукту немає.
                 Два рівні тексту, нуль графіки.
  2 чого бракує  кадр болю без продукту: стіл після вечері. Три рівні, буліти.
  3 омега-3      одна буквальна метафора: золота капсула на просвіт + банка.
  4 магній       той самий макет, інша метафора й палітра — кристал солі.
  5 як приймати  форма вживання замість упаковки: склянка, чотири капсули.
                 Єдиний кадр, де дозволені іконки.
  6 тридцять днів  календар без продукту, гігантська цифра.
  7 фінал        обидві банки без рамки, найщільніший текст, ціна.

Наскрізний лічильник «ЩОДЕННА ОСНОВА · N / 7» — прийом із серій хлорели
та спіруліни. Шрифт один на всю карусель, акцентних кольорів не більше двох,
текст ніде не лягає на етикетку.
"""
import sys
from pathlib import Path

ROOT = Path(r"D:\Клод код\Инстаграм публикации")
sys.path.insert(0, str(ROOT / "src"))

import fullgen as F
import generate as gen
import build_day as B
from render_html import shot, data_uri

OUT = ROOT / "out" / "post_v3"
JARS = [ROOT / "out" / "real" / "all" / n for n in ("omega.jpg", "magnium.jpg")]
OMEGA = [ROOT / "out" / "real" / "all" / "omega.jpg"]
MAG = [ROOT / "out" / "real" / "all" / "magnium.jpg"]

INK = "#2f3128"
OLIVE = "#7b812b"
NAVY = "#2b3a5c"
TERRA = "#a8552c"
PAPER = "#f4f1e8"

PATTERN = ("plain off-white paper background (RGB 246 245 238) with a faint "
           "outlined botanical pattern — thin pale beige line drawings of "
           "mushrooms, leaves and roots, barely visible. ")

TAIL = (" Bright even daylight, soft natural shadows, clean catalogue look, no "
        "dark corners. NO TEXT anywhere in the image except wording printed on "
        "the product packaging.")

SCENES = {
    "1_обкладинка": (
        "Extreme macro photograph, no product and no packaging at all: a single "
        "drop of warm golden oil unfurling in cold clear water, lit from behind "
        "so the drop glows amber against deep blue-grey, fine bubbles around it. "
        "The UPPER THIRD is calm and darker for text." + TAIL, None),

    "2_чого-бракує": (
        "Editorial photograph, no product and no packaging at all: a wooden "
        "dinner table after a meal in the evening — an empty plate with a fork "
        "left on it, a crumpled napkin, a half-empty glass of water, warm lamp "
        "light from the side, the rest of the table bare. Quiet, slightly "
        "melancholic. The LEFT HALF stays empty and dark for text." + TAIL, None),

    "3_омега": (
        PATTERN + "Behind the product a soft watercolour blot in muted "
        "terracotta with visible paper texture. The fish oil jar from the "
        "attached photo stands on the RIGHT, and next to it, very large and "
        "sharp, one translucent golden capsule lit from behind so the oil "
        "inside glows. A few more capsules lie around. The LEFT HALF is empty "
        "paper with the pattern only." + TAIL, OMEGA),

    "4_магній": (
        PATTERN + "Behind the product a soft watercolour blot in deep navy "
        "blue with visible paper texture. The magnesium jar from the attached "
        "photo stands on the LEFT, and next to it, very large and sharp, one "
        "raw grey mineral salt crystal catching the light. A few smaller "
        "crystals lie around. Everything — jar, crystals, blot and every "
        "shadow — stays STRICTLY LEFT of the vertical centre line and does not "
        "touch it. The RIGHT HALF is bare paper with the faint pattern only: "
        "no blot, no colour wash, no object, no shadow." + TAIL, MAG),

    "5_як-приймати": (
        PATTERN + "A glass of water stands on the paper, and in front of it "
        "four capsules lie in a neat row on a linen napkin: two translucent "
        "golden ones and two white ones. The two jars from the attached photos "
        "stand behind, out of focus and CROPPED by the right edge of the frame. "
        "The TOP HALF is empty paper with the pattern only." + TAIL, JARS),

    "6_тридцять-днів": (
        PATTERN + "No product, no packaging, no calendar, no numbers and no "
        "lettering at all: just the bare patterned paper sheet lying flat, with "
        "a single olive-green pencil lying along the very BOTTOM edge of the "
        "frame, horizontally, its shadow soft. Nothing else. Seen straight "
        "down, bright even light. The upper three quarters of the sheet stay "
        "completely clean and empty — a grid of numbers will be printed there "
        "later." + TAIL, None),

    "7_фінал": (
        PATTERN + "Behind the products a wide soft watercolour blot, terracotta "
        "blending into navy. Both jars from the attached photos stand together "
        "in the LOWER HALF, centred, seen straight on, large and sharp, with no "
        "frame around them. Golden capsules and grey crystals lie at their base. "
        "The TOP THIRD is empty paper with the pattern only." + TAIL, JARS),
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
 letter-spacing:.24em;text-transform:uppercase;color:%s}
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


def counter(n, dark=False):
    return ("<div class='cnt'><span>Щоденна основа</span><i></i>"
            "<span>%d / 7</span></div>" % n)


def page(css, body):
    return ("<html><head>%s<style>%s</style></head><body>"
            "<div class='bg'></div>%s</body></html>" % (FONTS, css, body))


def build(tag, bg):
    n = int(tag[0])
    if tag.startswith("1"):
        # два рівні тексту, нуль графіки, світлий текст на темній воді
        css = base(bg, dark=True) + """
.col{position:absolute;left:6.4%;right:14%;top:13%}
h1{font-size:96px}p{font-size:34px;margin-top:22px;opacity:.92;max-width:80%}
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(8,14,20,.82) 0%,rgba(8,14,20,.6) 26%,rgba(8,14,20,.24) 46%,
 rgba(8,14,20,0) 64%)}
"""
        body = ("<div class='sh'></div>" + counter(n, True) +
                "<div class='col'><h1>Щоденна<br>основа</h1>"
                "<p>Щодня. Без екзотики. Рівно місяць.</p></div>")

    elif tag.startswith("2"):
        # кадр болю: три рівні, буліти, текст на темній половині
        css = base(bg, dark=True) + """
.col{position:absolute;left:6.4%;top:15%;width:50%}
h1{font-size:70px}
.rule{width:140px;background:#f4f1e8;opacity:.6}
li{font-size:31px}
p{font-size:27px;opacity:.8;margin-top:8px;font-style:italic}
.sh{position:absolute;inset:0;background:linear-gradient(96deg,
 rgba(10,12,16,.9) 0%,rgba(10,12,16,.86) 26%,rgba(10,12,16,.62) 48%,
 rgba(10,12,16,.28) 66%,rgba(10,12,16,0) 84%)}
"""
        body = ("<div class='sh'></div>" + counter(n, True) +
                "<div class='col'><h1>Двох речей<br>бракує<br>найчастіше</h1>"
                "<div class='rule'></div><ul>"
                "<li>Жирна морська риба на столі буває рідко</li>"
                "<li>Магній витрачається швидше, ніж здається</li>"
                "</ul><p>І це не про дієту, а про звичайний тиждень.</p></div>")

    elif tag.startswith("3"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:17%;width:42%}
h1{font-size:74px;color:#a8552c}h2{font-size:32px;margin-top:12px}
.rule{width:150px;background:#a8552c}
p{font-size:31px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Омега-3</h1>"
                "<h2>риб'ячий жир</h2><div class='rule'></div>"
                "<p>Те, що організм не робить сам і бере тільки з їжі. "
                "У капсулі — той самий жир, лише без запаху риби.</p></div>")

    elif tag.startswith("4"):
        # той самий макет, дзеркально, інша палітра — прийом «шаблон-конструктор»
        css = base(bg) + """
.col{position:absolute;right:6.4%;top:17%;width:38%;text-align:right}
h1{font-size:74px;color:#2b3a5c}h2{font-size:32px;margin-top:12px}
.rule{width:150px;background:#2b3a5c;margin-left:auto}
p{font-size:31px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Магній</h1>"
                "<h2>у формі гліцинату</h2><div class='rule'></div>"
                "<p>Мінерал, який іде зі стресом і потом. Гліцинат — форма, "
                "яку переносять мʼякше за оксид.</p></div>")

    elif tag.startswith("5"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:11%;width:50%}
h1{font-size:66px}
.rule{width:140px;background:#7b812b}
.s{display:flex;align-items:flex-start;margin-bottom:26px}
.s em{flex:0 0 54px;height:54px;border:2px solid #7b812b;border-radius:50%;
 font-style:normal;font-weight:800;font-size:26px;color:#7b812b;
 display:flex;align-items:center;justify-content:center;margin-right:20px}
.s b{display:block;font-weight:800;font-size:34px;text-transform:uppercase;
 letter-spacing:-.3px}
.s span{display:block;font-weight:500;font-size:26px;margin-top:3px}
"""
        body = (counter(n) +
                "<div class='col'><h1>Як приймати</h1><div class='rule'></div>"
                "<div class='s'><em>2</em><div><b>З банки омеги</b>"
                "<span>під час їжі</span></div></div>"
                "<div class='s'><em>2</em><div><b>З банки магнію</b>"
                "<span>того самого дня</span></div></div>"
                "<div class='s'><em>4</em><div><b>Разом на добу</b>"
                "<span>щодня, без пропусків</span></div></div></div>")

    elif tag.startswith("6"):
        css = base(bg) + """
.col{position:absolute;left:6.4%;top:15%;width:38%}
.big{font-weight:800;font-size:230px;color:#7b812b;line-height:.8;
 letter-spacing:-10px}
h2{font-size:46px;margin-top:14px}
.rule{width:160px;background:#7b812b}
p{font-size:30px}
.grid{position:absolute;right:6.4%;top:22%;width:44%;display:grid;
 grid-template-columns:repeat(5,1fr);gap:18px 10px}
.d{font-weight:600;font-size:30px;color:#2f3128;opacity:.62;text-align:center;
 line-height:56px}
.d.last{opacity:1;color:#7b812b;font-weight:800;position:relative}
.d.last:after{content:'';position:absolute;left:50%;top:50%;width:62px;
 height:62px;margin:-31px 0 0 -31px;border:4px solid #7b812b;border-radius:50%}
"""
        days = "".join(
            "<div class='d%s'>%d</div>" % (" last" if d == 30 else "", d)
            for d in range(1, 31))
        body = (counter(n) +
                "<div class='col'><div class='big'>30</div>"
                "<h2>днів і жодного<br>залишку</h2><div class='rule'></div>"
                "<p>У кожній банці 60 капсул. По дві на добу з кожної — "
                "обидві закінчаться в один день.</p></div>"
                "<div class='grid'>" + days + "</div>")

    else:
        # найщільніший кадр каруселі: підводка, назва, склад, три буліти, ціна
        css = base(bg) + """
.col{position:absolute;left:6.4%;right:6.4%;top:9%;text-align:center}
.eye{font-weight:600;font-size:20px;letter-spacing:.26em;text-transform:uppercase;
 color:#7b812b}
h1{font-size:72px;margin-top:14px}
h2{font-size:30px;margin-top:10px;font-weight:600;color:#5c5f52;
 text-transform:none;letter-spacing:0}
.rule{width:140px;background:#7b812b;margin:20px auto 18px}
.row{display:flex;justify-content:center;gap:34px;font-weight:600;font-size:25px}
.row span:not(:last-child):after{content:' ·';opacity:.45}
.price{position:absolute;left:0;right:0;bottom:6%;text-align:center}
.price b{font-weight:800;font-size:56px;color:#a8552c;letter-spacing:-1px}
.price s{font-weight:600;font-size:36px;color:#7d7f74;margin-left:18px;
 text-decoration-thickness:3px}
.price small{display:block;font-weight:500;font-size:25px;color:#2f3128;
 margin-top:10px;letter-spacing:0}
"""
        body = (counter(n) +
                "<div class='col'><div class='eye'>Курс на місяць</div>"
                "<h1>Щоденна основа</h1>"
                "<h2>омега-3 риб'ячий жир і магній гліцинат</h2>"
                "<div class='rule'></div>"
                "<div class='row'><span>60 + 60 капсул</span>"
                "<span>4 на добу</span><span>30 днів</span></div></div>"
                "<div class='price'><b>927 грн</b><s>1030 грн</s>"
                "<small>за обидві банки · посилання в шапці профілю</small></div>")
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
                prompt += (" The jars keep their own labels: ЛІСОВИК, ОМЕГА-3 "
                           "РИБ'ЯЧИЙ ЖИР, МАГНІЙ ГЛІЦИНАТ. No other small print.")
                ok = F.draw_ref(prompt, refs, tok, bg, aspect="4:5")
            else:
                ok = F.draw_raw(prompt, tok, bg, aspect="4:5")
            print(("  ✔ фон " if ok else "  ✖ фон ") + tag, flush=True)
        if bg.exists():
            html = build(tag, bg)
            shot(html, OUT / (tag + ".png"))
            shot(html.replace("</style>", ".col,.price{visibility:hidden}</style>"),
                 OUT / "_blank" / (tag + ".png"))
            print("  ✔ кадр", tag, flush=True)
    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
