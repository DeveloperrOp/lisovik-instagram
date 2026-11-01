# -*- coding: utf-8 -*-
"""Сторіс тижня 11: «гербарій на шалфеї», подача «паперова картка».

Ярик 01.11 обрав подачу A з пʼяти проб: текст кадру факту лежить на
кремовій картці, приклеєній стрічкою до аркуша гербарію, без градієнта —
підкладка тижня 10 вибілювала верх упаковки. Надзаголовок — жовтий чіп
цілі, як на картках товарів нового сайту (#F7E8B4).

Тло, промпти, етикетки продажу й оферти — з build_story_v8 без змін.

    python build_story_v9.py ../content/day11_ginkgo.yaml
    python build_story_v9.py ../content/day11_ginkgo.yaml --compose --only dawn
"""
import re
import sys
from pathlib import Path

from PIL import Image

import build_story_v8 as V8
import fullgen as F
import generate as gen
from config import CONTENT_DIR, OUT_DIR
from render_html import shot, data_uri

esc = V8.esc

CARD_CSS = """
.wash{display:none}
.card{position:absolute;left:6%;right:6%;top:5%;background:#FBF8EF;
 padding:46px 50px 50px;transform:rotate(-0.8deg);
 box-shadow:0 18px 40px -26px rgba(30,34,20,.5)}
.card:before,.card:after{content:'';position:absolute;width:130px;height:38px;
 background:rgba(236,226,200,.85);top:-19px}
.card:before{left:-20px;transform:rotate(-20deg)}
.card:after{right:-20px;transform:rotate(18deg)}
.chip{display:inline-block;background:#F7E8B4;color:#24272B;border-radius:12px;
 padding:10px 18px;font-family:Manrope;font-weight:800;font-size:24px;
 letter-spacing:.05em;text-transform:uppercase}
.card h1{margin-top:26px}
.card p{margin-top:24px;max-width:100%}
"""


# Ярик 01.11: «а где подход с вайбом про людей в кадре». Маленька людина на
# аркуші гербарію повертає вайб сайту (тиждень 9) — у ранку й продажі, поле
# person у файлі дня. Масштаб — правила тижня 9, що тримались найкраще.
SCALE = (" A tiny real person is part of the scene, like a miniature figure on "
         "a giant herbarium sheet: the product is about THREE times taller "
         "than the person, and the top of the person's head is lower than the "
         "middle of the product. The person is clearly visible and does not "
         "cover the product label.")


def scene_prompt(p: dict, t: dict) -> str:
    if t.get("person"):
        own = " ".join(str(t["subject"]).split()) + " " + \
            " ".join(str(t["person"]).split())
        return V8.jar_prompt(p, dict(t, subject=own)).replace(
            V8.TAIL, SCALE + V8.TAIL)
    return V8.jar_prompt(p, t)


def sizes(t: dict) -> dict:
    c, n = len(t.get("claim") or ""), len(t.get("why") or "")
    return {"@H1@": str(92 if c <= 26 else 84 if c <= 34 else 76),
            "@P@": str(37 if n <= 120 else 35 if n <= 170 else 33)}


def render(p: dict, t: dict, bg: Path) -> str:
    body = ("<div class='card'><span class='chip'>" + esc(p["plaque"]) +
            "</span><h1>" + esc(t.get("claim")) + "</h1>")
    if t.get("why"):
        body += "<p>" + esc(" ".join(str(t["why"]).split())) + "</p>"
    body += "</div>"
    # Продаж і оферта — етикетка гербарію тижня 10 унизу, але заголовок теж
    # на картці: перша проба 01.11 лишала їх на градієнті, і день виглядав
    # зібраним із двох тижнів.
    if t["layout"] in ("sell", "offer"):
        html = V8.render(p, t, bg)
        head = re.search(r"<div class='col'>.*?</div>(?=<div class='lab'>)", html, re.S)
        sz = sizes(t)
        css = CARD_CSS + (".card h1{font-size:%spx}.card p{font-size:%spx}"
                          % (sz["@H1@"], sz["@P@"]))
        html = html.replace(head.group(0), body).replace("</style>", css + "</style>")
        return html.replace("<div class='wash'></div>", "")
    if t.get("do"):
        body += "<div class='hand'>" + esc(t["do"]) + "</div>"
    css = V8.CSS.replace("@BG@", data_uri(bg)).replace("@LW@", "60") + CARD_CSS
    for k, v in sizes(t).items():
        css = css.replace(k, v)
    return ("<html><head>" + V8.FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div>" + body + "</body></html>")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day11_ginkgo.yaml")
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
                ok = F.draw_raw(V8.specimen_prompt(t), tok, bg, aspect="9:16")
            else:
                ok = F.draw_ref(scene_prompt(p, t),
                                [OUT_DIR / "real" / "all" / p["ref"]], tok, bg,
                                aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            png = chk / f"{t['key']}.png"
            shot(render(p, t, bg), png, w=V8.W, h=V8.H, wait=1800)
            Image.open(png).convert("RGB").save(outdir / f"{t['key']}.jpg",
                                                "JPEG", quality=92)
            print("  ✔ кадр", t["key"], flush=True)
    print("тека:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
