# -*- coding: utf-8 -*-
"""Сторіс тижня 8: «вода і скло». Вайб обрав Ярик 11.10 з трьох проб.

Холодна блакить, мокре скло, краплі й заломлення. Темно-синя
типографіка по світлому, під заголовком — коротка хвиля замість
плашки. Вайб виріс із продукту: тремела у воді набухає в кілька разів.

Свідома протилежність попереднім тижням:

  тижні 1-2  плакат із жовтою плашкою;
  тижні 3-4  світлий папір із візерунком і піщана розкладка;
  тиждень 5  темна студія з золотою плашкою заголовка;
  тиждень 6  білий мінімал, чорна типографіка, порожнє поле;
  тиждень 7  теракота й камінь, кремовий гротеск (відкладений);
  тиждень 8  вода і скло, холодна блакить.

Половина кадрів іде без банки — там сама сировина. Що класти в кадр,
вирішує поле subject у файлі дня.

🚨 Дозувань у текстах цього тижня немає навмисно: на сторіс їх не
ставимо. В омеги й магнію через це зник головний аргумент-цифра, тому
розмова там про принцип — що шукати на етикетці.

    python build_story_v6.py ../content/day8_tremela.yaml
    python build_story_v6.py ../content/day8_tremela.yaml --compose
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

INK = "#10303f"
DIM = "#2d5567"
ACC = "#4b8aa6"
DARK = "#e2f0f6"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' "
         "rel='stylesheet'>")

STONE = ("Editorial still life in cool pale blue light on a wet glass "
         "surface, clear water droplets and soft refractions, condensation, "
         "calm and clean. ")
TAIL = (" NO TEXT anywhere in the image except wording printed on the product "
        "packaging. No stamps, seals or badges in the background. Crisp and "
        "editorial.")
# 🚨 Вайб «вода і скло» читається моделлю як косметика, і вона підставляє
# чужі бренди замість нашої упаковки: у першій спробі вийшли флакон Aesop
# і банка Nature's Answer. Референс сам по собі цього не спиняє, тому
# упаковку доводиться описувати словами й забороняти чужі марки прямо.
def keep_for(t: dict) -> str:
    """Опис упаковки словами — його мало не вистачити.

    Референс сам по собі моделі не наказ: у вайбі «вода і скло» вона
    читає кадр як косметику й підставляє чужі марки. У першій спробі
    вийшли флакон Aesop і банка Nature's Answer — обидва чужі бренди в
    нашій стрічці. Тому упаковка описується словами, а чужі марки
    забороняються прямо.
    """
    pack = " ".join((t.get("pack") or "").split())
    if not pack or not shows_pack(t):
        return ""
    return (" CRITICAL: the product is EXACTLY the one in the attached photo "
            "and belongs to the Ukrainian brand ЛІСОВИК: " + pack +
            ", carrying the white ЛІСОВИК tree-face logo. It is NOT a glass "
            "dropper bottle, NOT a pump bottle and NOT a cosmetics "
            "container. The label carries ONLY the big product name and that "
            "logo: NO small print lines, NO paragraph of fine text, NO "
            "barcode, NO ingredient list anywhere on the package.")


# 🚨 Чужа марка лізе й туди, де нашої упаковки в кадрі немає: на макро
# капсул магнію модель надрукувала «NATURE'S SERENITY · CALM & FOCUS»
# просто по оболонці. Тому заборона йде окремим рядком у КОЖЕН кадр, а
# не тільки в ті, де описана банка.
NOBRAND = (" ABSOLUTELY NO brand name, logo, slogan or wording of any other "
           "company anywhere in the image, and no English brand text of any "
           "kind. Capsules, berries, powder and raw material are completely "
           "bare: nothing is printed or stamped on them. NO barcode, NO QR "
           "code, NO block of fine print anywhere in the image.")


# 🚨 Раніше наявність товару в кадрі шукалась як «jar» у subject. Тремела
# лежить у pouch, детокс у box — для них умова ніколи не спрацьовувала, і
# обидва дні малювались без референсу взагалі.
# «product» тут головне слово: саме ним у файлах дня названа наша
# упаковка — «the product from the attached photo». Без нього перевірка
# не бачила товару майже ніде й кадр малювався без референсу: на місці
# нашого пакета тремели вийшла китайська банка з ієрогліфами.
PACKWORDS = ("product", "attached photo", "jar", "bottle", "pouch", "box",
             "package", "packet", "sachet")


def shows_pack(t: dict) -> bool:
    own = (t.get("subject") or "").lower()
    return any(w in own for w in PACKWORDS)


EMPTY = (" The UPPER TWO THIRDS of the frame are smooth pale blue — no object, "
         "no shadow, nothing at all. The BOTTOM TENTH is bare too: nothing "
         "reaches the lower edge.")
ONE = (" There is EXACTLY ONE jar in the frame: no second bottle, no "
       "duplicate, no reflection of another one.")


def scene_for(t: dict) -> str:
    """Сцена під слот. Поверхня й світло спільні, міняється композиція."""
    slot = t.get("slot")
    own = " ".join((t.get("subject") or "").split())
    # Кадр без банки описує саму сировину — тоді й заборона на другу
    # банку ні до чого.
    one = ONE if shows_pack(t) else ""

    if slot == "morning":
        return (STONE + "FLAT LAY, camera directly overhead: " + own +
                " Every object lies flat on the wet glass, nothing stands "
                "upright." + one + EMPTY + TAIL + keep_for(t) + NOBRAND)
    if slot == "noon":
        return (STONE + "Extreme macro, razor sharp: " + own + " The object "
                "fills the MIDDLE of the frame, large and detailed." + EMPTY +
                TAIL + keep_for(t) + NOBRAND)
    if slot == "evening":
        return (STONE + own + " Seen slightly from the side, one long hard "
                "reflection falling to the right across the wet glass." + one +
                EMPTY + TAIL + keep_for(t) + NOBRAND)
    return (STONE + own + " SMALL, standing in the LOWER MIDDLE of the frame "
            "but clearly ABOVE the bottom edge, with a clear empty gap of "
            "space between the object and the bottom, seen straight on. The "
            "package is far from the camera and takes up no more than one "
            "quarter of the image height; its fine print is too small to "
            "read." + one + EMPTY + TAIL + keep_for(t) + NOBRAND)


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


HEAD = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Montserrat;overflow:hidden;
 position:relative;color:@INK@;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(226,240,246,.95) 0%,rgba(226,240,246,.78) 36%,rgba(226,240,246,0) 56%)}
.col{position:absolute;left:8%;right:8%;top:6%}
.eye{font-weight:700;font-size:25px;letter-spacing:.3em;text-transform:uppercase;
 color:@ACC@;margin-bottom:24px}
h1{font-weight:700;text-transform:uppercase;line-height:.96;letter-spacing:-2px}
h1:after{content:'';display:block;width:130px;height:4px;background:@ACC@;
 margin-top:22px;border-radius:2px}
.do{position:absolute;left:8%;bottom:6%;font-weight:700;font-size:29px;
 letter-spacing:.14em;text-transform:uppercase;color:@INK@;
 border-bottom:4px solid @ACC@;padding-bottom:13px}
"""

FILL = """
h1{font-size:@H1@px}
p{font-weight:500;font-size:@P@px;line-height:1.36;margin-top:@PT@px;
 max-width:90%;color:@DIM@}
"""

LIST = """
h1{font-size:88px}
ul{list-style:none;margin-top:40px}
li{font-weight:600;font-size:40px;line-height:1.3;padding:20px 0;
 border-bottom:1px solid rgba(75,138,166,.3);color:@DIM@}
"""


def sizes(why: str) -> dict:
    """Кегль під довжину підпису — тут до 230 знаків."""
    n = len(why)
    p = 40 if n <= 80 else 37 if n <= 130 else 35 if n <= 180 else 33
    h1 = 96 if n <= 130 else 88
    return {"@P@": str(p), "@PT@": "28", "@H1@": str(h1)}


def render(t: dict, bg: Path) -> str:
    claim, why, do = esc(t.get("claim")), esc(t.get("why")), esc(t.get("do"))
    topic = esc(t.get("topic", ""))
    parts = [x.strip() for x in (t.get("extra") or "").split("|") if x.strip()]

    if parts:
        css = HEAD + LIST
        rows = "".join("<li>" + esc(x) + "</li>" for x in parts)
        body = ("<div class='col'><div class='eye'>" + topic + "</div>"
                "<h1>" + claim + "</h1><ul>" + rows + "</ul></div>")
    else:
        css = HEAD + FILL
        for k, v in sizes(why).items():
            css = css.replace(k, v)
        body = ("<div class='col'><div class='eye'>" + topic + "</div>"
                "<h1>" + claim + "</h1><p>" + why + "</p></div>")

    css = (css.replace("@BG@", data_uri(bg)).replace("@INK@", INK)
              .replace("@DIM@", DIM).replace("@ACC@", ACC)
              .replace("@DARK@", DARK))
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div><div class='wash'></div>" + body +
            "<div class='do'>" + do + "</div></body></html>")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day8_tremela.yaml")
    items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]

    offers = {o["day"]: o for o in yaml.safe_load(
        (CONTENT_DIR / "offers.yaml").read_text(encoding="utf-8"))["offers"]}
    day = items[0].get("day")
    if day in offers:
        o = offers[day]
        have = " ".join(t.get("topic", "") for t in items).lower()

        def fits(x):
            w = (x.get("product") or "").lower()
            return not w or w[:5] in have

        if not fits(o):
            same = [x for k, x in offers.items()
                    if k.startswith(day) and k != day and fits(x)]
            o = same[0] if same else next(
                (x for x in offers.values() if fits(x)), o)
        items = items + [dict(o, key=f"{path.stem}-offer", slot="night",
                              topic=items[0].get("topic", ""),
                              ref=items[0].get("ref"), why="", compound="",
                              subject=items[0].get("subject"),
                              # Без опису упаковки оферта малювалась як
                              # косметика з чужим брендом: поле pack до неї
                              # не доходило, бо кадр додається окремо.
                              pack=items[0].get("pack"),
                              source="content/offers.yaml")]

    outdir = OUT_DIR / path.stem
    chk = outdir / "_chk"
    blank = chk / "_blank"
    blank.mkdir(parents=True, exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()

    for t in items:
        bg = outdir / f"bg_{t['key']}.png"
        if not bg.exists() and tok:
            refs = [OUT_DIR / "real" / "all" / r for r in (t.get("ref") or [])]
            prompt = scene_for(t)
            # Кадр без банки малюється без референсу: поки фото
            # прикріплене, модель однаково ставить банку в кадр.
            if refs and shows_pack(t):
                prompt += " " + " ".join(B.REF_MANY.split())
                ok = F.draw_ref(prompt, refs, tok, bg, aspect="9:16")
            else:
                ok = F.draw_raw(prompt, tok, bg, aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            html = render(t, bg)
            png = chk / f"{t['key']}.png"
            shot(html, png, w=W, h=H)
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
