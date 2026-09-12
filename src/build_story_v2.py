# -*- coding: utf-8 -*-
"""Сторіс у макетах, які обрав Ярик 12.09: D «макро-капсула» і E «розкладка».

Старий build_day малює плакати з жовтою плашкою — той дизайн відпрацював.
Тут інша мова, знята з обраних варіантів:

  D — велика прозора капсула або сировина крупним планом, текст угорі,
      кнопка-пігулка внизу, тло — світлий папір із контурним візерунком;
  E — розкладка згори на теплому піщаному тлі, велика цифра в кутку,
      темна кнопка на всю ширину.

Макети чергуються по слотах, щоб день не читався як шість однакових
екранів: dawn і noon — D, morning і evening — E, sell — товарний кадр,
night — оферта дня.

    python build_story_v2.py ../content/day4_triichatka.yaml
    python build_story_v2.py ../content/day4_triichatka.yaml --compose

Текст береться з того самого YAML, що й раніше, і проходить check_thought.
"""
import sys
from pathlib import Path

import yaml
from PIL import Image

import build_day as B
import fullgen as F
import generate as gen
from config import CONTENT_DIR, OUT_DIR
from render_html import shot, data_uri

W, H = 1080, 1920

INK = "#2f3128"
FOREST = "#2f4a2c"
OLIVE = "#7b812b"
CREAM = "#f6f2e6"
SAND = "#c8764f"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")

# Яким макетом малюється слот
LAYOUT = {"dawn": "D", "morning": "E", "noon": "D", "evening": "E",
          "sell": "S", "night": "N"}

PAPER = ("plain off-white paper background (RGB 246 245 238) with a faint "
         "outlined botanical pattern — thin pale beige line drawings of leaves "
         "and roots, barely visible. ")
SANDBG = ("plain warm sand-terracotta seamless surface, even soft light, no "
          "pattern. ")
TAIL = (" NO TEXT anywhere in the image except wording printed on the product "
        "packaging. No stamps, seals, round badges, certification marks or "
        "logos anywhere in the background or on the surface: the product's own "
        "label is the ONLY printed thing in the frame. "
        "Soft natural shadows, clean catalogue look.")

# Друга банка в кадрі — найчастіший брак цього макета, тому заборона
# формулюється окремо й прямо.
ONEJAR = ("There is EXACTLY ONE jar in the entire frame: no second jar, no "
          "duplicate, no smaller copy in a corner, no reflection of another "
          "jar. If hands are in the frame, there are exactly TWO hands and "
          "they belong to one person; nobody pours capsules out of the jar.")


def scene_for(t: dict, jar_hint: str) -> str:
    """Сцена під макет слоту. Композиція задана жорстко, бо текст лягає
    у конкретну зону, і предмет туди заходити не повинен."""
    kind = LAYOUT.get(t.get("slot"), "D")
    own = " ".join((t.get("subject") or "").split())
    # Банку описує сама сцена кадру. Раніше макет дописував їй ще одну
    # «в нижньому куті» — і в кадрі стояло дві банки; Ярик спіймав це на
    # першому й третьому кадрі трійчатки. Тепер макет банку не додає,
    # тільки забороняє другу.
    if kind == "D":
        return (PAPER + "Extreme macro: " + own + " The objects fill the MIDDLE "
                "of the frame, enormous and razor sharp. " + ONEJAR +
                " The TOP THIRD is bare patterned paper, completely empty." + TAIL)
    if kind == "E":
        return (SANDBG + "Seen straight down: " + own + " The raw material is "
                "laid out in neat small heaps. " + ONEJAR +
                " The TOP THIRD is bare empty surface." + TAIL)
    if kind == "S":
        return (PAPER + own + " " + ONEJAR + " The TOP THIRD is bare patterned "
                "paper, completely empty." + TAIL)
    return (PAPER + "EXACTLY ONE jar stands in the LOWER HALF, centred, seen "
            "straight on, with a wide soft watercolour blot behind it in deep "
            "forest green. The TOP THIRD is bare patterned paper, completely "
            "empty." + TAIL)


def page(css: str, uri: str, body: str) -> str:
    return ("<html><head>%s<style>*{margin:0;padding:0;box-sizing:border-box}"
            # Сіре згладжування замість субпіксельного: інакше по краю
            # кожного вертикального штриха лягає кольорова бахрома —
            # (241,195,110) там, де літера темно-сіра. Оку вона майже не
            # видно, а check_readable рахував ту бахрому за штрих і
            # звітував про нечитабельний текст на чистому білому папері.
            "body{width:%dpx;height:%dpx;font-family:Montserrat;overflow:hidden;"
            "position:relative;-webkit-font-smoothing:antialiased}"
            ".bg{position:absolute;inset:0;background:url('%s') center/cover}"
            "h1{font-weight:800;text-transform:uppercase;letter-spacing:-2px;"
            "line-height:.95}"
            "%s</style></head><body><div class='bg'></div>%s</body></html>"
            % (FONTS, W, H, uri, css, body))


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


def render(t: dict, bg: Path) -> str:
    kind = LAYOUT.get(t.get("slot"), "D")
    uri = data_uri(bg)
    claim, why, do = esc(t.get("claim")), esc(t.get("why")), esc(t.get("do"))
    topic = esc(t.get("topic", ""))

    if kind in ("D", "S"):
        css = """
h1{font-size:86px;color:%s}
.eye{font-weight:600;font-size:30px;color:%s;letter-spacing:.2em;
 text-transform:uppercase;margin-bottom:18px}
p{font-weight:400;font-size:40px;line-height:1.34;color:%s;margin-top:26px;
 max-width:88%%}
.col{position:absolute;left:7%%;right:7%%;top:6%%}
.do{position:absolute;left:7%%;bottom:5.5%%;font-weight:700;font-size:34px;
 color:#fdfbf4;background:%s;padding:20px 34px;border-radius:999px;
 text-transform:uppercase}
""" % (FOREST, OLIVE, INK, FOREST)
        body = ("<div class='col'><div class='eye'>%s</div><h1>%s</h1>"
                "<p>%s</p></div><div class='do'>%s</div>"
                % (topic, claim, why, do))

    elif kind == "E":
        # Текст ТЕМНИЙ: піщано-теракотове тло виходить світлим, і кремові
        # літери на ньому зливались із фоном — заміряно (243,200,168) проти
        # (244,205,176), тобто контрасту не було взагалі.
        css = """
h1{font-size:82px;color:%s}
.eye{font-weight:600;font-size:29px;color:rgba(47,74,44,.75);
 letter-spacing:.2em;text-transform:uppercase;margin-bottom:16px}
p{font-weight:400;font-size:38px;line-height:1.34;color:%s;
 margin-top:24px;max-width:86%%}
.col{position:absolute;left:7%%;right:7%%;top:6.5%%}
.do{position:absolute;left:7%%;right:7%%;bottom:5.5%%;text-align:center;
 font-weight:800;font-size:34px;color:#fdfbf4;background:%s;padding:24px;
 border-radius:16px;text-transform:uppercase}
""" % (FOREST, INK, FOREST)
        body = ("<div class='col'><div class='eye'>%s</div><h1>%s</h1>"
                "<p>%s</p></div><div class='do'>%s</div>"
                % (topic, claim, why, do))

    else:  # оферта дня
        parts = [x.strip() for x in (t.get("extra") or "").split("|") if x.strip()]
        rows = "".join("<li>%s</li>" % esc(x) for x in parts)
        css = """
h1{font-size:80px;color:%s;text-align:center}
.col{position:absolute;left:8%%;right:8%%;top:7%%}
ul{list-style:none;margin-top:26px}
li{font-weight:600;font-size:33px;line-height:1.28;color:%s;text-align:center;
 padding:13px 0;border-bottom:1px solid rgba(47,74,44,.2)}
.do{position:absolute;left:7%%;right:7%%;bottom:5.5%%;text-align:center;
 font-weight:800;font-size:34px;color:#fdfbf4;background:%s;padding:24px;
 border-radius:16px;text-transform:uppercase}
""" % (FOREST, INK, FOREST)
        body = ("<div class='col'><h1>%s</h1><ul>%s</ul></div>"
                "<div class='do'>%s</div>" % (claim, rows, do))

    return page(css, uri, body)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day4_triichatka.yaml")
    items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]

    # оферта дня додається так само, як у сторіс попередніх тижнів
    offers = {o["day"]: o for o in yaml.safe_load(
        (CONTENT_DIR / "offers.yaml").read_text(encoding="utf-8"))["offers"]}
    day = items[0].get("day")
    if day in offers:
        o = offers[day]
        # Оферта, привʼязана до конкретного продукту, у чужому дні брехлива:
        # у дні трійчатки стояв заголовок «ОДИН ГРИБ — КІЛЬКА ФОРМ» із
        # прикріпленим їжовиком. Беремо наступну, яка нічого конкретного
        # не називає. Та сама перевірка, що в build_day.
        have = " ".join(t.get("topic", "") for t in items).lower()

        def fits(x):
            w = (x.get("product") or "").lower()
            return not w or w[:5] in have

        if not fits(o):
            o = next((x for x in offers.values() if fits(x)), o)
        items = items + [dict(o, key=f"{path.stem}-offer", slot="night",
                              topic=items[0].get("topic", ""),
                              ref=items[0].get("ref"), why="", compound="",
                              source="content/offers.yaml")]

    outdir = OUT_DIR / path.stem
    outdir.mkdir(parents=True, exist_ok=True)
    # PNG-пара для чекера читабельності живе окремо від кадрів,
    # які йдуть у публікацію.
    chk = outdir / "_chk"
    blank = chk / "_blank"
    blank.mkdir(parents=True, exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()

    for t in items:
        bg = outdir / f"bg_{t['key']}.png"
        if not bg.exists() and tok:
            refs = [OUT_DIR / "real" / "all" / r for r in (t.get("ref") or [])]
            prompt = scene_for(t, "")
            if refs:
                prompt += " " + " ".join(B.REF_MANY.split())
                ok = F.draw_ref(prompt, refs, tok, bg, aspect="9:16")
            else:
                ok = F.draw_raw(prompt, tok, bg, aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            html = render(t, bg)
            # Знімаємо в PNG, а JPEG робимо конвертацією. Playwright пише
            # jpeg якістю 80, і навколо великих літер лишається ореол;
            # check_readable порівнює кадр із підкладкою піксель у піксель
            # і бачив той ореол як темний фон під літерою — чистий кадр
            # із контрастом 9 показувало як 1.35.
            png = chk / f"{t['key']}.png"
            shot(html, png, w=W, h=H)
            # Підкладка без тексту — щоб чекер знайшов літери й заміряв,
            # на чому вони лежать. Ховаємо САМІ ЛІТЕРИ, а не блоки: у
            # кнопки .do є своя темна плашка, і visibility:hidden прибирав
            # її разом із текстом — тоді білі літери мірялись проти
            # фотографії, а не проти плашки, на якій вони лежать.
            shot(html.replace("</style>",
                              ".col,.col *,.do{color:transparent!important}"
                              "</style>"),
                 blank / f"{t['key']}.png", w=W, h=H)
            Image.open(png).convert("RGB").save(
                outdir / f"{t['key']}.jpg", "JPEG", quality=92)
            print("  ✔ кадр", t["key"], flush=True)

    print("тека:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
