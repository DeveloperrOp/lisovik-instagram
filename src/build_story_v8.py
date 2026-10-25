# -*- coding: utf-8 -*-
"""Сторіс тижня 10: «гербарій на шалфеї». Обрав Ярик 25.10 з восьми проб.

Аркуш гербарію на шалфейному папері сайту (#DCE5D2): засушений зразок на
стрічках, порожня бирка, вид згори. Шрифти сайту — Manrope і Wix Madefor.

  тиждень 9   шалфей, банка-велетень, біла плашка сайту на кожному кадрі;
  тиждень 10  гербарій на шалфеї, БЕЗ однакової плашки внизу.

Ярик 25.10: «мені не подобається однотипна плашка внизу, яка була на
кожному фото минулого тижня» і «дивись склад на сайті — бездумно з тижня в
тиждень». Тому:

  кадр факту (dawn, morning, noon, evening) закінчується фактом; поле do
  лише тоді, коли факт сам дає практичну пораду, — і тоді це рукописна
  позначка ботаніка, а не плашка;
  продаж (sell) і форми (оферта) — етикетка гербарію: ярлик у рамці,
  приклеєний стрічкою, з латинською назвою.

    python build_story_v8.py ../content/day10_maca.yaml
    python build_story_v8.py ../content/day10_maca.yaml --compose
    python build_story_v8.py ../content/day10_maca.yaml --only dawn,sell
"""
import sys
from pathlib import Path

import yaml
from PIL import Image

import fullgen as F
import generate as gen
from config import CONTENT_DIR, OUT_DIR
from render_html import shot, data_uri

W, H = 1080, 1920

FONTS = ("<link href='https://fonts.googleapis.com/css2?family=Manrope:wght@700;800"
         "&family=Wix+Madefor+Text:wght@500&family=Lora:ital,wght@1,500"
         "&family=Caveat:wght@700&display=swap' rel='stylesheet'>")

# 25.10: у продажу спіруліни друк на пакеті вийшов подвоєним і змазаним —
# Ярик побачив мило одразу. Різкість і цілісність друку названо прямо.
SHEET = ("Vintage herbarium sheet photographed flat from directly above, on "
         "smooth light sage-green matte paper (#DCE5D2): soft even daylight, "
         "calm, clean, archival mood. Everything is tack-sharp and in focus, "
         "no blur, no ghosting. ")
# 25.10, перша партія тижня 10: модель друкувала власні етикетки гербарію
# («COLLECTED 2023 NEW YORK», «FLORA MEDICINALIS 1887») і докладала чужі
# рослини — морську водорость до спіруліни, чебрець до хлорели.
TAIL = (" Every tag, card, label, slide or envelope in the image is BLANK — no "
        "printed or handwritten words, no captions, no specimen labels with "
        "writing. NO text anywhere except the wording printed on the product "
        "itself. No plant, herb, seaweed, mushroom or spice that is not named "
        "in this description. No other brand name, logo or English brand text "
        "anywhere. No red-and-white spotted mushrooms. No cannabis or hemp "
        "leaves, no marijuana plants of any kind. No pills or capsules lying "
        "loose.")
# 🚨 25.10, повтор продажу спіруліни: модель сама зібрала «гербарну
# колекцію» й намалювала листок коноплі з ярликом «Hemp leavers». Для Meta
# це категорія наркотиків — бан BM, як із мухомором. Заборона тепер у
# кожному кадрі.


def specimen_prompt(t: dict) -> str:
    own = " ".join((t.get("subject") or "").split())
    return (SHEET + own + " The UPPER 42% of the frame is bare sage paper, "
            "completely empty." + TAIL)


def jar_prompt(p: dict, t: dict) -> str:
    own = " ".join((t.get("subject") or "").split())
    pack = " ".join((p.get("pack") or "").split())
    # Етикетка продажу й оферти лягає на низ — там має бути порожньо.
    low = (" The BOTTOM 22% is bare sage paper too."
           if t["layout"] in ("sell", "offer") else "")
    return (SHEET + own + " The product is EXACTLY the one in the attached "
            "photo: " + pack + " Reproduce its label as in the photo, printed "
            "once, crisp and sharp — no doubled or smeared print. Do not "
            "include the glass stand from the photo. EXACTLY ONE product in "
            "the frame, and the whole product, including its top edge, sits "
            "below the upper 42%. The UPPER 42% of the frame is bare sage "
            "paper, completely empty." + low + TAIL)


def esc(s) -> str:
    return (str(s) if s is not None else "").replace("&", "&amp;") \
        .replace("<", "&lt;")


CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;
 font-family:'Wix Madefor Text';color:#15171A;background:#DCE5D2}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(220,229,210,.93),rgba(220,229,210,.72) 32%,rgba(220,229,210,0) 48%)}
.col{position:absolute;left:8%;right:8%;top:6.5%}
.eye{font-family:Manrope;font-weight:800;font-size:26px;letter-spacing:.08em;
 text-transform:uppercase;color:#5A8326}
h1{font-family:Manrope;font-weight:800;font-size:@H1@px;line-height:1.03;
 letter-spacing:-2.2px;margin-top:24px}
p{font-weight:500;font-size:@P@px;line-height:1.42;margin-top:30px;
 color:#3B4148;max-width:95%}
.hand{position:absolute;left:9%;right:9%;bottom:7%;font-family:Caveat;
 font-weight:700;font-size:60px;line-height:1.05;color:#4f6f22;
 transform:rotate(-3deg)}
.hand:after{content:'';display:block;width:62%;height:10px;margin-top:6px;
 border-bottom:4px solid #4f6f22;border-radius:0 0 60% 40%}
.lab{position:absolute;left:7%;bottom:5%;width:@LW@%;background:#FBF8EF;
 border:2px solid #2b2d24;padding:26px 32px 28px;transform:rotate(-1.2deg);
 box-shadow:0 12px 26px -16px rgba(30,34,20,.45)}
.lab:before,.lab:after{content:'';position:absolute;width:110px;height:34px;
 background:rgba(236,226,200,.8);top:-17px}
.lab:before{left:-26px;transform:rotate(-24deg)}
.lab:after{right:-26px;transform:rotate(22deg)}
.plq{font-family:Manrope;font-weight:800;font-size:22px;letter-spacing:.08em;
 text-transform:uppercase;color:#5A8326}
.nm{font-family:Manrope;font-weight:800;font-size:46px;margin-top:6px}
.row{display:flex;justify-content:space-between;align-items:baseline;gap:20px;
 margin-top:6px}
.lat{font-family:Lora;font-style:italic;font-weight:500;font-size:32px;
 color:#2b2d24}
.pr{font-family:Manrope;font-weight:800;font-size:54px;white-space:nowrap}
.rule{height:1px;background:#2b2d24;opacity:.45;margin:14px 0}
.sm{font-weight:500;font-size:25px;color:#3B4148}
.li{display:flex;justify-content:space-between;gap:20px;font-family:Manrope;
 font-weight:700;font-size:32px;padding:10px 0;
 border-bottom:1px solid rgba(43,45,36,.18)}
.li b{font-weight:800;color:#5A8326;white-space:nowrap}
"""


def sizes(t: dict) -> dict:
    c, n = len(t.get("claim") or ""), len(t.get("why") or "")
    return {"@H1@": str(104 if c <= 26 else 94 if c <= 34 else 86),
            "@P@": str(40 if n <= 90 else 38 if n <= 150 else 36)}


def render(p: dict, t: dict, bg: Path) -> str:
    lay = t["layout"]
    body = ("<div class='col'><div class='eye'>" + esc(p["name"]) + "</div>"
            "<h1>" + esc(t.get("claim")) + "</h1>")
    if t.get("why"):
        body += "<p>" + esc(" ".join(str(t["why"]).split())) + "</p>"
    body += "</div>"
    lw = "60"
    if lay == "sell":
        lw = "68"
        body += ("<div class='lab'><div class='plq'>" + esc(p["plaque"]) +
                 "</div><div class='nm'>" + esc(p["name"]) + "</div>"
                 "<div class='row'><div class='lat'>" + esc(p["latin"]) +
                 "</div>" + ("<div class='pr'>" + esc(p["price"]) + " ₴</div>"
                             if p.get("price") else "") + "</div>"
                 "<div class='rule'></div><div class='sm'>" + esc(t.get("do")) +
                 " · посилання в шапці профілю</div></div>")
    elif lay == "offer":
        lw = "74"
        rows = ""
        for x in (t.get("extra") or "").split("|"):
            x = " ".join(x.split())
            if x:
                a, _, b = x.partition(" — ")
                rows += ("<div class='li'><span>" + esc(a) + "</span>" +
                         ("<b>" + esc(b) + "</b>" if b else "") + "</div>")
        body += ("<div class='lab'><div class='lat'>" + esc(p["latin"]) +
                 "</div><div class='rule'></div>" + rows +
                 "<div class='sm' style='margin-top:16px'>" + esc(t.get("do")) +
                 "</div></div>")
    elif t.get("do"):
        body += "<div class='hand'>" + esc(t["do"]) + "</div>"

    css = CSS.replace("@BG@", data_uri(bg)).replace("@LW@", lw)
    for k, v in sizes(t).items():
        css = css.replace(k, v)
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div><div class='wash'></div>" + body +
            "</body></html>")


def load(path: Path):
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    items = list(d["thoughts"])
    if d.get("offer"):
        items.append(dict(d["offer"], key=f"{path.stem}-offer", slot="night"))
    return d["product"], items


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "day10_maca.yaml")
    p, items = load(path)
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
                ok = F.draw_ref(jar_prompt(p, t),
                                [OUT_DIR / "real" / "all" / p["ref"]], tok, bg,
                                aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            png = chk / f"{t['key']}.png"
            shot(render(p, t, bg), png, w=W, h=H, wait=1800)
            Image.open(png).convert("RGB").save(
                outdir / f"{t['key']}.jpg", "JPEG", quality=92)
            print("  ✔ кадр", t["key"], flush=True)
    print("тека:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
