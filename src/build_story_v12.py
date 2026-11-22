# -*- coding: utf-8 -*-
"""Тиждень 14: «зимовий ярмарок» — та сама паперова картка (v9), новий світ.

Ярик 22.11 обрав із трьох зимових проб ярмарок: засніжений дерев'яний стіл,
маленькі дерев'яні ятки з гірляндами, ковзанка, сніг, маленькі люди.

Головна зміна проти v10/v11: Ярик помітив, що люди в кожному дні робили те
саме (плед, листок, книжка). Тут типової сценки НЕМАЄ — поле crew у кожному
кадрі обов'язкове, а check_crews() не пускає тиждень, у якому одна дія
повторюється двічі.
  specimen  — на ярмарку сировина (гриб, ягоди, трава), банки немає;
  jar/sell/offer — на ярмарку банка, довкола люди.

    python build_story_v12.py ../content/day14_chaga.yaml
    python build_story_v12.py ../content/day14_chaga.yaml --only dawn,sell
    python build_story_v12.py ../content/day14_chaga.yaml --compose
    python build_story_v12.py --check-week 14
"""
import glob
import re
import sys
from pathlib import Path

import yaml
from PIL import Image

import build_story_v8 as V8
import build_story_v9 as V9
import fullgen as F
import generate as gen
from config import CONTENT_DIR, OUT_DIR
from render_html import shot

FAIR = ("A miniature WINTER FAIR on a snowy wooden table at blue evening: tiny "
        "wooden market stalls with snow-covered roofs and warm string lights, "
        "the stalls have NO signs and NO writing at all, gentle falling snow, "
        "a soft blurred winter window behind. Everything on the table is "
        "tack-sharp and in focus. ")

SCALE_JAR = (" The tiny people are real people photographed like miniature "
             "figures in winter coats, hats and scarves: each one is shorter "
             "than ONE FIFTH of the product's height, and none of them covers "
             "the product label. Every person does a DIFFERENT action, exactly "
             "as listed — no two people do the same thing.")
SCALE_RAW = (" The tiny people are real people photographed like miniature "
             "figures in winter coats, hats and scarves: each one is shorter "
             "than ONE THIRD of the height of the main object and does not hide "
             "it. Every person does a DIFFERENT action, exactly as listed.")

TOP = (" The UPPER 42% of the frame is calm and empty — only soft blurred "
       "snowy evening background, no objects, no people, no stalls.")
SIZE = (" The product is clearly the HERO: it stands in front of the stalls, "
        "about one quarter of the frame height, in the middle band between "
        "46% and 76% of the frame height; the stalls are small and behind it.")
LOW = " The BOTTOM 22% of the frame is plain snowy table, empty."
NO_FIRE = " No candles, no bonfires, no open flame."


def flat(x) -> str:
    return " ".join(str(x or "").split())


def specimen_prompt(t: dict) -> str:
    return (FAIR + flat(t["subject"]) + " " + flat(t["crew"]) + SCALE_RAW +
            " NO product, jar, bottle, box or package anywhere in the frame." +
            TOP + NO_FIRE + V8.TAIL)


# 22.11: в оферті картка з 3–4 рядками вища, ніж у продажі, і закривала
# половину банки разом із назвою. Тому в оферті банка стоїть вище.
SIZE_OFFER = (" The product is clearly the HERO and stands HIGHER than usual: "
              "about one quarter of the frame height, between 40% and 62% of the "
              "frame height, fully visible from lid to bottom; the tiny people "
              "stand beside it at the same level.")
LOW_OFFER = (" The BOTTOM 38% of the frame is plain snowy table, completely "
             "empty — no people, no objects.")


def scene_prompt(p: dict, t: dict) -> str:
    if t["layout"] == "offer":
        size, low = SIZE_OFFER, LOW_OFFER
    else:
        size = SIZE
        low = LOW if t["layout"] == "sell" else ""
    return (FAIR + flat(t["subject"]) + " " + flat(t["crew"]) +
            " The product is EXACTLY the one in the attached photo: " +
            flat(p["pack"]) + " Reproduce its label as in the photo, printed "
            "once, crisp and sharp — no doubled or smeared print. The attached "
            "photo is ONLY a reference for the package itself: do NOT copy its "
            "background, props or stand. EXACTLY ONE product in the frame (or "
            "exactly the set described)." + size + SCALE_JAR + TOP + low +
            NO_FIRE + V8.TAIL)


def actions(crew: str) -> list:
    """Дії з поля crew: «one skates…, two carry…» → нормалізовані фрази."""
    body = flat(crew).split(":", 1)[-1]
    parts = re.split(r"[;,.]\s*(?:and\s+)?", body)
    out = []
    for x in parts:
        x = re.sub(r"^(one|two|three|a|an|the|another)\s+", "", x.strip().lower())
        x = re.sub(r"^(tiny\s+)?(man|woman|child|girl|boy|person|people|couple)\s+", "", x)
        if len(x) > 6:
            out.append(" ".join(x.split()[:4]))
    return out


def check_crews(n: str) -> int:
    """Жодна дія не повторюється в межах тижня."""
    seen, bad = {}, 0
    for f in sorted(glob.glob(str(CONTENT_DIR / f"day{n}_*.yaml"))):
        d = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
        items = list(d["thoughts"]) + ([dict(d["offer"], key=Path(f).stem + "-offer")]
                                       if d.get("offer") else [])
        for t in items:
            if not t.get("crew"):
                print(f"  ✖ {t['key']}: немає crew")
                bad += 1
                continue
            for a in actions(t["crew"]):
                if a in seen and seen[a] != t["key"]:
                    print(f"  ✖ «{a}»: {seen[a]} і {t['key']}")
                    bad += 1
                seen.setdefault(a, t["key"])
    print(f"дій: {len(seen)} | повторів: {bad}")
    return 1 if bad else 0


def main() -> int:
    if "--check-week" in sys.argv:
        return check_crews(sys.argv[sys.argv.index("--check-week") + 1])
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day14_chaga.yaml")
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
        assert t.get("crew"), f"{t['key']}: немає crew — сценка має бути своя"
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
