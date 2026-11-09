# -*- coding: utf-8 -*-
"""Тиждень 12: «фотостудія» замість гербарію — та сама паперова картка (v9),
але світ навколо інший.

Ярик 09.11 обрав із шести напрямів фотостудію, а з шести студійних сюжетів —
«зйомку сировини»: шавлієвий безшовний фон, білий подіум, маленька знімальна
група. Тому однаковий світ на всіх кадрах дня:
  specimen  — на подіумі сировина (гриб, цвіт, мінерал), банки немає;
  jar/sell/offer — на подіумі сама банка, довкола група.
Хто саме в кадрі й що робить — поле crew у файлі дня; без нього — типова
група. Масштаб людей — з проб 09.11, де він тримався найкраще.

    python build_story_v10.py ../content/day12_shiitake.yaml
    python build_story_v10.py ../content/day12_shiitake.yaml --only dawn,sell
    python build_story_v10.py ../content/day12_shiitake.yaml --compose
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

STUDIO = ("A clean miniature PHOTO SHOOT on a seamless pale sage-green paper "
          "backdrop (#C9D6BE) with a soft curve from wall to floor, bright "
          "soft studio light, gentle shadows. Everything is tack-sharp and in "
          "focus, no blur. ")

CREW = ("Five tiny people form the photo crew around it: a photographer with "
        "a camera on a tripod, an assistant holding a round white reflector, "
        "a lighting tech next to a softbox on a stand, a stylist adjusting "
        "the subject with a soft brush, a director pointing.")

# Масштаб — перевірене на пробах 09.11: «менше пʼятої частини банки».
SCALE_JAR = (" The tiny people are real people photographed like miniature "
             "figures: each one is shorter than ONE FIFTH of the product's "
             "height, and none of them covers the product label. They are "
             "clearly visible, sharp, with natural poses.")
SCALE_RAW = (" The tiny people are real people photographed like miniature "
             "figures: each one is shorter than ONE THIRD of the height of the "
             "object on the pedestal and does not hide it. They are clearly "
             "visible, sharp, with natural poses.")

TOP = (" The UPPER 42% of the frame is plain empty sage backdrop — no "
       "objects, no people, no light stands reaching into it.")
# Перша проба продажу 09.11: банка на пів кадру, кришка пішла під картку, а
# фотограф — під етикетку. Тут вільна лише смуга між карткою й етикеткою.
LOW = (" The BOTTOM 22% of the frame is plain empty sage floor too. The "
       "product is about 28% of the frame height and stands in the middle "
       "band, between 44% and 76% of the frame height; the tiny people "
       "stand in the same band, beside the pedestal, not below it.")


def flat(x) -> str:
    return " ".join(str(x or "").split())


def specimen_prompt(t: dict) -> str:
    return (STUDIO + flat(t["subject"]) + " " + flat(t.get("crew") or CREW) +
            SCALE_RAW + " NO product, jar, bottle, box or package anywhere "
            "in the frame." + TOP + V8.TAIL)


def scene_prompt(p: dict, t: dict) -> str:
    low = LOW if t["layout"] in ("sell", "offer") else ""
    return (STUDIO + flat(t["subject"]) + " " + flat(t.get("crew") or CREW) +
            " The product is EXACTLY the one in the attached photo: " +
            flat(p["pack"]) + " Reproduce its label as in the photo, printed "
            "once, crisp and sharp — no doubled or smeared print. The attached "
            "photo is ONLY a reference for the package itself: do NOT copy "
            "its background, flowers, sea, stones, blur or colours — the "
            "whole scene is the plain sage studio. EXACTLY ONE "
            "product in the frame (or exactly the set described), and the "
            "whole product, including its top edge, sits below the upper 42%." +
            SCALE_JAR + TOP + low + V8.TAIL)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day12_shiitake.yaml")
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
