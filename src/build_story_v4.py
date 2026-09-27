# -*- coding: utf-8 -*-
"""Сторіс тижня 6: білий мінімал. Вайб обрав Ярик 27.09 з чотирьох проб.

Майже білий кадр, продукт маленький унизу, величезний чорний заголовок
угорі й жодних плашок. Це свідома протилежність попереднім тижням:

  тижні 1-2  плакат із жовтою плашкою;
  тижні 3-4  світлий папір із візерунком і піщана розкладка;
  тиждень 5  темна студія з золотою плашкою заголовка;
  тиждень 6  білий мінімал, чорна типографіка, порожнє поле.

Заклик унизу підкреслений лінією, а не залитий кнопкою: суцільна плашка
поверталася б до мови попередніх тижнів.

Композиція чергується по слотах, щоб день не читався як шість однакових
екранів, але тло й світло лишаються ті самі:

  dawn     продукт малий, по центру внизу
  morning  розкладка згори на білому
  noon     макро сировини, продукту в кадрі немає
  evening  продукт збоку, довга мʼяка тінь
  sell     товарний кадр зі списком
  night    оферта дня

    python build_story_v4.py ../content/day6_mind.yaml
    python build_story_v4.py ../content/day6_mind.yaml --compose
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

INK = "#13140f"
GREY = "#4d4d45"
FAINT = "#8f8f86"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")

WHITE = ("Minimal studio photograph on a seamless pure white background, "
         "bright, soft and almost shadowless, nothing else in the frame. ")
TAIL = (" NO TEXT anywhere in the image except wording printed on the product "
        "packaging. No stamps, seals or badges in the background. "
        "Crisp, clean, catalogue-like.")
KEEP = (" The product keeps its own printed label exactly as in the attached "
        "photo. Draw no other small print on it.")
EMPTY = (" The UPPER TWO THIRDS of the frame are empty white — no object, no "
         "shadow, nothing at all. The BOTTOM TENTH of the frame is empty "
         "white too: nothing reaches the lower edge.")

# Другий екземпляр товару в кадрі — найчастіший брак; для наборів із
# трьох банок заборона знімається.
ONE = (" There is EXACTLY ONE of the product in the frame: no second bottle, "
       "no second jar, no duplicate, no reflection of another one.")


def scene_for(t: dict) -> str:
    """Сцена під слот. Тло й світло спільні, міняється композиція."""
    slot = t.get("slot")
    own = " ".join((t.get("subject") or "").split())
    many = own.lower().startswith(("three jars", "four small", "a few dried"))
    one = "" if many else ONE

    if slot == "morning":
        return (WHITE + "FLAT LAY, camera directly overhead: " + own +
                " Every object lies flat on the white surface, nothing stands "
                "upright." + one + EMPTY + TAIL + KEEP)
    if slot == "noon":
        # Кадр без продукту: макро самої сировини на білому.
        return (WHITE + "Extreme macro, razor sharp: " + own + " The object "
                "fills the MIDDLE of the frame, large and detailed." + EMPTY +
                TAIL)
    if slot == "evening":
        return (WHITE + own + " Seen slightly from the side, one long soft "
                "shadow falling to the right across the white." + one + EMPTY +
                TAIL + KEEP)
    return (WHITE + own + " SMALL, standing in the BOTTOM CENTRE of the frame, "
            "seen straight on." + one + EMPTY + TAIL + KEEP)


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


HEAD = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Montserrat;overflow:hidden;
 position:relative;color:@INK@;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(255,255,255,.92) 0%,rgba(255,255,255,.78) 26%,rgba(255,255,255,0) 46%)}
.col{position:absolute;left:7%;right:7%;top:6%}
.eye{font-weight:700;font-size:26px;letter-spacing:.3em;text-transform:uppercase;
 color:@FAINT@;margin-bottom:24px}
h1{font-weight:800;text-transform:uppercase;line-height:.9}
.do{position:absolute;left:7%;bottom:6%;font-weight:800;font-size:34px;
 letter-spacing:.06em;text-transform:uppercase;color:@INK@;
 border-bottom:5px solid @INK@;padding-bottom:10px}
"""

FILL = """
h1{font-size:@H1@px;letter-spacing:-4px}
p{font-weight:500;font-size:@P@px;line-height:1.34;margin-top:@PT@px;
 max-width:88%;color:@GREY@}
"""

LIST = """
h1{font-size:96px;letter-spacing:-3px}
ul{list-style:none;margin-top:38px}
li{font-weight:600;font-size:40px;line-height:1.3;padding:18px 0;
 border-bottom:1px solid rgba(19,20,15,.14);color:@GREY@}
"""


def sizes(claim: str, why: str) -> dict:
    """Кегль під довжину тексту — підпис тут до 210 знаків."""
    n = len(why)
    p = 44 if n <= 70 else 40 if n <= 110 else 37 if n <= 160 else 34
    top = 34 if n <= 70 else 30 if n <= 160 else 26
    return {"@P@": str(p), "@PT@": str(top), "@H1@": "96"}


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
        for k, v in sizes(claim, why).items():
            css = css.replace(k, v)
        body = ("<div class='col'><div class='eye'>" + topic + "</div>"
                "<h1>" + claim + "</h1><p>" + why + "</p></div>")

    css = (css.replace("@BG@", data_uri(bg)).replace("@INK@", INK)
              .replace("@GREY@", GREY).replace("@FAINT@", FAINT))
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div><div class='wash'></div>" + body +
            "<div class='do'>" + do + "</div></body></html>")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day6_mind.yaml")
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
            if refs:
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
