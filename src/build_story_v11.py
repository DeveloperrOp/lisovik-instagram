# -*- coding: utf-8 -*-
"""Тиждень 13: «осіння веранда» — та сама паперова картка (v9), новий світ.

Ярик 16.11 обрав із трьох осінніх проб веранду: стіл біля вікна з краплями
дощу, теплий світ лампи, вʼязаний плед, чашка чаю, опале листя й маленькі
люди. Як і в студії (v10):
  specimen  — на столі сировина (корінь, ягоди, трава), банки немає;
  jar/sell/offer — на столі сама банка, довкола люди.
Хто в кадрі й що робить — поле crew у файлі дня; без нього — типова сценка.

У пробах 16.11 банка виходила на пів кадру й залазила під картку, тому
розмір і смуга задані явно для всіх кадрів з банкою, а не лише для продажу.

    python build_story_v11.py ../content/day13_gastro.yaml
    python build_story_v11.py ../content/day13_gastro.yaml --only dawn,sell
    python build_story_v11.py ../content/day13_gastro.yaml --compose
"""
import sys
from pathlib import Path

from PIL import Image

import build_story_v8 as V8
import build_story_v9 as V9
import fullgen as F
import generate as gen
from config import CONTENT_DIR, OUT_DIR
from render_html import shot

VERANDA = ("A cosy miniature AUTUMN VERANDA scene: an old wooden table by a "
           "window with raindrops on the glass, warm soft light from a lamp, "
           "a knitted cream wool blanket folded on the table, a few fallen "
           "orange and yellow maple leaves. Shallow depth of field behind, "
           "but everything on the table is tack-sharp and in focus. ")

CREW = ("Five tiny people in autumn sweaters and coats around it: one "
        "wrapped in a corner of the blanket, two carrying a big orange "
        "maple leaf together, one reading a small book, one pointing at the "
        "subject.")

SCALE_JAR = (" The tiny people are real people photographed like miniature "
             "figures: each one is shorter than ONE FIFTH of the product's "
             "height, and none of them covers the product label. They are "
             "clearly visible, sharp, with natural poses.")
SCALE_RAW = (" The tiny people are real people photographed like miniature "
             "figures: each one is shorter than ONE THIRD of the height of the "
             "main object and does not hide it. They are clearly visible, "
             "sharp, with natural poses.")

TOP = (" The UPPER 42% of the frame is calm and empty — only the soft "
       "blurred window and wall, no objects, no people, no lamp.")
SIZE = (" The product is SMALL: about one quarter of the frame height, and "
        "it stands in the middle band, between 46% and 76% of the frame "
        "height; the tiny people stand in the same band beside it.")
LOW = " The BOTTOM 22% of the frame is plain empty wooden table."
# Проба веранди 16.11: свічка поруч із людьми — гарно, але вогонь біля
# фігурок читається тривожно. Лампа дає те саме тепло.
NO_FIRE = " No candles, no open flame."


def flat(x) -> str:
    return " ".join(str(x or "").split())


def specimen_prompt(t: dict) -> str:
    return (VERANDA + flat(t["subject"]) + " " + flat(t.get("crew") or CREW) +
            SCALE_RAW + " NO product, jar, bottle, box or package anywhere "
            "in the frame." + TOP + NO_FIRE + V8.TAIL)


def scene_prompt(p: dict, t: dict) -> str:
    low = LOW if t["layout"] in ("sell", "offer") else ""
    return (VERANDA + flat(t["subject"]) + " " + flat(t.get("crew") or CREW) +
            " The product is EXACTLY the one in the attached photo: " +
            flat(p["pack"]) + " Reproduce its label as in the photo, printed "
            "once, crisp and sharp — no doubled or smeared print. The attached "
            "photo is ONLY a reference for the package itself: do NOT copy "
            "its background or props. EXACTLY ONE product in the frame (or "
            "exactly the set described)." + SIZE + SCALE_JAR + TOP + low +
            NO_FIRE + V8.TAIL)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day13_gastro.yaml")
    p, items = V8.load(path)
    only = sys.argv[sys.argv.index("--only") + 1].split(",") \
        if "--only" in sys.argv else None
    outdir = OUT_DIR / path.stem
    chk = outdir / "_chk"
    chk.mkdir(parents=True, exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()
    for t in items:
        if only and t["slot"] not in only:
            continue
        bg = outdir / f"bg_{t['key']}.png"
        if not bg.exists() and tok:
            if t["layout"] == "specimen":
                ok = F.draw_raw(specimen_prompt(t), tok, bg, aspect="9:16")
            else:
                ok = F.draw_ref(scene_prompt(p, t),
                                [OUT_DIR / "real" / "all" / p["ref"]], tok, bg,
                                aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            png = chk / f"{t['key']}.png"
            shot(V9.render(p, t, bg), png, w=V8.W, h=V8.H, wait=1800)
            Image.open(png).convert("RGB").save(outdir / f"{t['key']}.jpg",
                                                "JPEG", quality=92)
            print("  ✔ кадр", t["key"], flush=True)
    print("тека:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
