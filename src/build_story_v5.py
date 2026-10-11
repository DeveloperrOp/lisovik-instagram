# -*- coding: utf-8 -*-
"""Сторіс тижня 7: «камінь». Вайб обрав Ярик 11.10 з трьох проб.

Теракотова шерехата поверхня, холодне бокове світло, довгі жорсткі
тіні, землисті тони. Великий гротеск кремовим по теплому тлу, заклик —
персиковою плашкою. Свідома протилежність попереднім тижням:

  тижні 1-2  плакат із жовтою плашкою;
  тижні 3-4  світлий папір із візерунком і піщана розкладка;
  тиждень 5  темна студія з золотою плашкою заголовка;
  тиждень 6  білий мінімал, чорна типографіка, порожнє поле;
  тиждень 7  теракота й камінь, кремовий гротеск.

Тиждень про традицію й історію: половина кадрів іде без банки — там
саме сировина, корінь або капелюшок, бо розмова про те, що з цим
робили предки, а не про фасовку. Що класти в кадр, вирішує поле
subject у файлі дня.

    python build_story_v5.py ../content/day7_maca.yaml
    python build_story_v5.py ../content/day7_maca.yaml --compose
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

INK = "#f4ece1"
DIM = "rgba(244,236,225,.88)"
ACC = "#e0a475"
DARK = "#3a2116"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' "
         "rel='stylesheet'>")

STONE = ("Editorial still life on a rough terracotta-coloured stone slab, "
         "cool high-altitude daylight raking from the left, long hard "
         "shadows, warm earthy tones. ")
TAIL = (" NO TEXT anywhere in the image except wording printed on the product "
        "packaging. No stamps, seals or badges in the background. Crisp and "
        "editorial.")
KEEP = (" The product keeps its own printed label exactly as in the attached "
        "photo. Draw no other small print on it.")
EMPTY = (" The UPPER TWO THIRDS of the frame are bare terracotta stone — no "
         "object, no shadow, nothing at all. The BOTTOM TENTH is bare stone "
         "too: nothing reaches the lower edge.")
ONE = (" There is EXACTLY ONE jar in the frame: no second bottle, no "
       "duplicate, no reflection of another one.")


def scene_for(t: dict) -> str:
    """Сцена під слот. Поверхня й світло спільні, міняється композиція."""
    slot = t.get("slot")
    own = " ".join((t.get("subject") or "").split())
    # Кадр без банки описує саму сировину — тоді й заборона на другу
    # банку ні до чого.
    one = "" if "jar" not in own.lower() else ONE

    if slot == "morning":
        return (STONE + "FLAT LAY, camera directly overhead: " + own +
                " Every object lies flat on the stone, nothing stands "
                "upright." + one + EMPTY + TAIL + KEEP)
    if slot == "noon":
        return (STONE + "Extreme macro, razor sharp: " + own + " The object "
                "fills the MIDDLE of the frame, large and detailed." + EMPTY +
                TAIL)
    if slot == "evening":
        return (STONE + own + " Seen slightly from the side, one long hard "
                "shadow falling to the right across the stone." + one +
                EMPTY + TAIL + KEEP)
    return (STONE + own + " SMALL, standing in the LOWER MIDDLE of the frame "
            "but clearly ABOVE the bottom edge, with a clear empty gap of "
            "stone between the object and the bottom, seen straight on." +
            one + EMPTY + TAIL + KEEP)


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


HEAD = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Montserrat;overflow:hidden;
 position:relative;color:@INK@;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(58,33,22,.92) 0%,rgba(58,33,22,.66) 36%,rgba(58,33,22,0) 56%)}
.col{position:absolute;left:8%;right:8%;top:6%}
.eye{font-weight:700;font-size:25px;letter-spacing:.3em;text-transform:uppercase;
 color:@ACC@;margin-bottom:24px}
h1{font-weight:800;text-transform:uppercase;line-height:.94;letter-spacing:-2.5px}
.do{position:absolute;left:8%;bottom:6%;font-weight:800;font-size:31px;
 letter-spacing:.07em;text-transform:uppercase;color:@DARK@;
 background:@ACC@;padding:19px 28px;border-radius:3px}
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
 border-bottom:1px solid rgba(224,164,117,.34);color:@DIM@}
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
    path = Path(args[0] if args else CONTENT_DIR / "day7_maca.yaml")
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
            # Кадр без банки малюється без референсу: поки фото
            # прикріплене, модель однаково ставить банку в кадр.
            if refs and "jar" in (t.get("subject") or "").lower():
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
