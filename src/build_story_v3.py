# -*- coding: utf-8 -*-
"""Сторіс тижня 5: темна студія. Вайб і типографіку обрав Ярик 20.09.

Тло: майже чорне з зеленуватим підтоном, один жорсткий теплий промінь
збоку, продукт вирізаний із темряви, пил у промені. Це заміна світлому
паперу з візерунком, який відпрацював чотири тижні.

Типографіка — варіант D із проби: заголовок темними літерами на золотій
плашці, підпис світлим на тлі, заклик унизу під тонкою лінією. Суцільної
кнопки більше немає: вона робила кадр схожим на банер.

Композиція чергується по слотах, щоб день не читався як шість однакових
екранів, але світло й палітра лишаються ті самі:

  dawn     герой: продукт у промені, текст угорі
  morning  розкладка згори на темній поверхні
  noon     макро сировини, продукт позаду
  evening  герой збоку, промінь ззаду
  sell     товарний кадр зі списком
  night    оферта дня

    python build_story_v3.py ../content/day5_lysychka.yaml
    python build_story_v3.py ../content/day5_lysychka.yaml --compose
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

CREAM = "#f4f1e6"
GOLD = "#d9a441"
INK = "#12180f"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?"
         "family=Montserrat:wght@400;500;600;700;800&display=swap' rel='stylesheet'>")

DARK = ("Cinematic studio still life on a deep near-black background with a "
        "faint dark-green undertone, seamless, no props and no furniture. ")
BEAM = (" Lit by ONE hard warm beam of light from the upper left, carving the "
        "objects out of deep shadow; fine dust drifts in the beam; everything "
        "else falls away into black.")
TAIL = (" NO TEXT anywhere in the image except wording printed on the product "
        "packaging. No stamps, seals or badges anywhere in the background. "
        "Rich contrast, premium catalogue look.")
KEEP = (" The product keeps its own printed label exactly as in the attached "
        "photo. Draw no other small print on it.")
EMPTY = " The TOP 45% of the frame is almost black and completely empty."

# Друга банка в кадрі — найчастіший брак цього макета, тому заборона
# формулюється окремо й прямо. Для курсу з трьох банок вона знімається.
ONEJAR = (" There is EXACTLY ONE jar in the entire frame: no second jar, no "
          "duplicate, no smaller copy in a corner.")


def scene_for(t: dict) -> str:
    """Сцена під слот. Світло й палітра спільні, міняється композиція."""
    slot = t.get("slot")
    own = " ".join((t.get("subject") or "").split())
    many = own.lower().startswith("three jars")
    one = "" if many else ONEJAR

    if slot == "morning":
        return (DARK + "FLAT LAY, camera directly overhead looking straight "
                "down at the surface: " + own + " Every object LIES FLAT on "
                "the surface, nothing stands upright, and the whole "
                "composition is seen from above." + BEAM + one + EMPTY +
                TAIL + KEEP)
    if slot == "noon":
        # Кадр без продукту: макро самої сировини. Тому ні ONEJAR, ні KEEP —
        # у кадрі нема чого зберігати й нема чому дублюватись.
        return (DARK + "Extreme macro, razor sharp, shallow depth of field: "
                + own + " The objects fill the MIDDLE of the frame, enormous."
                + BEAM + EMPTY + TAIL)
    if slot == "evening":
        return (DARK + own + " Seen slightly from the side, the beam coming "
                "from behind and rimming the edges." + BEAM + one + EMPTY +
                TAIL + KEEP)
    # dawn, sell, night — герой прямо
    return (DARK + own + " Seen straight on, centred in the LOWER HALF." +
            BEAM + one + EMPTY + TAIL + KEEP)


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;")


HEAD = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Montserrat;overflow:hidden;
 position:relative;color:@CREAM@;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.sh{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(6,10,6,.92) 0%,rgba(6,10,6,.55) 30%,rgba(6,10,6,0) 52%,
 rgba(6,10,6,.35) 88%,rgba(6,10,6,.72) 100%)}
h1{font-weight:800;text-transform:uppercase;letter-spacing:-2px}
.col{position:absolute;left:0;right:0;top:6%}
.eye{font-weight:600;font-size:30px;color:@GOLD@;letter-spacing:.24em;
 text-transform:uppercase;margin:0 7% 22px}
.do{position:absolute;left:7%;right:7%;bottom:5.5%;padding-top:24px;
 border-top:2px solid rgba(217,164,65,.6);font-weight:800;font-size:38px;
 color:@CREAM@;text-transform:uppercase;letter-spacing:.03em}
"""

# Заголовок на золотій плашці: box-decoration-break:clone дає плашку по
# кожному рядку окремо, а не один прямокутник на весь блок.
FILL = """
h1{font-size:96px;color:@INK@;background:@GOLD@;display:inline;
 box-decoration-break:clone;-webkit-box-decoration-break:clone;
 padding:14px 22px;line-height:1.26;margin-left:7%}
p{font-weight:500;font-size:46px;line-height:1.3;margin:34px 7% 0;
 max-width:80%;color:rgba(244,241,230,.92)}
"""

LIST = """
h1{font-size:82px;color:@INK@;background:@GOLD@;display:inline;
 box-decoration-break:clone;-webkit-box-decoration-break:clone;
 padding:12px 20px;line-height:1.28;margin-left:7%}
ul{list-style:none;margin:36px 7% 0}
li{font-weight:600;font-size:40px;line-height:1.3;padding:16px 0;
 border-bottom:1px solid rgba(244,241,230,.18);color:rgba(244,241,230,.92)}
"""


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
        body = ("<div class='col'><div class='eye'>" + topic + "</div>"
                "<h1>" + claim + "</h1><p>" + why + "</p></div>")

    css = (css.replace("@BG@", data_uri(bg)).replace("@CREAM@", CREAM)
              .replace("@GOLD@", GOLD).replace("@INK@", INK))
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div><div class='sh'></div>" + body +
            "<div class='do'>" + do + "</div></body></html>")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day5_lysychka.yaml")
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
