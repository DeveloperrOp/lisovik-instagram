# -*- coding: utf-8 -*-
"""Сторіс тижня 9: «шалфей» — світ нового сайту. Обрав Ярик 19.10.

Фон — матовий шалфейний папір #DCE5D2, вид згори, мʼяке денне світло.
Типографіка й біла плашка — з нового сайту (Manrope, Wix Madefor Text,
картка вітрини .sc-cap). Два кадри дня, morning і sell, — банка-велетень
з маленькою людиною, як сцени вітрини; решта — сама сировина без банки.

  тиждень 8  вода і скло, холодна блакить;
  тиждень 9  шалфей, банка-велетень, типографіка сайту.

Промпт велетня — шаблон SCENE1 сайту (market/lisovik/tools/gen.mjs),
переведений у 9:16 з порожнім верхом під текст і низом під плашку.

Правило Ярика (10.10, сайт): дрібна одруківка на етикетці — не брак.
Брак — не та форма банки чи колір етикетки, друга банка, капсули поза
банкою, людина вища за пів банки.

🚨 Сторіс вічнозелені (Ярик 19.10): їх перевикористовують пізніше, тому
ні знижок, ні закресленої ціни, ні «цього тижня». Ціна на плашці лишається
— вона перескладається з --compose за секунду, якщо зміниться.

Нічний кадр (оферта) лежить у файлі дня, а не в offers.yaml: оферти
тижня 9 привʼязані до товару, а не до дня тижня. Ключ — «<файл>-offer»,
бо саме таке імʼя чекає queue_days.frames().

    python build_story_v7.py ../content/day9_mane.yaml
    python build_story_v7.py ../content/day9_mane.yaml --compose
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

INK = "#15171A"
DIM = "#3B4148"
MUTE = "#646A73"
OLIVE = "#5A8326"
SALE = "#D0312D"
SAGE = "#DCE5D2"

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?family=Manrope:"
         "wght@600;700;800&family=Wix+Madefor+Text:wght@400;500;600"
         "&display=swap' rel='stylesheet'>")

BASE = ("Photorealistic top-down flat-lay commercial photograph, vertical "
        "9:16 format.\n\nBackground: smooth light sage-green matte paper "
        "(#DCE5D2), soft diffused daylight, gentle natural shadows, calm, "
        "airy, fresh mood.")
# Мухомор домальовується сам на будь-який «лісовий гриб» — заборона в
# кожен кадр, а не тільки там, де гриб у сцені.
TAIL = ("Clean, minimal, premium commercial photography. Absolutely no text "
        "and no logos anywhere@LABEL@. No pills or capsules lying loose, no "
        "medical objects, no doctors, no sick people, no children. No "
        "red-and-white spotted mushrooms.")
NOBRAND = (" ABSOLUTELY NO brand name, logo, slogan or wording of any other "
           "company anywhere in the image, and no English brand text of any "
           "kind. Raw material and powder are completely bare: nothing is "
           "printed or stamped on them.")


def macro_prompt(t: dict) -> str:
    own = " ".join((t.get("subject") or "").split())
    return (BASE + "\n\n" + own[0].upper() + own[1:] + " The objects lie in "
            "the LOWER HALF of the frame. The UPPER 45% of the frame is "
            "completely empty smooth sage paper — no object, no leaf, no "
            "shadow, nothing at all.\n\n" + TAIL.replace("@LABEL@", "") +
            NOBRAND)


def giant_prompt(p: dict, t: dict) -> str:
    jar = " ".join((p.get("jar") or "").split())
    body = " ".join((t.get("body") or "").split())
    details = " ".join((t.get("details") or "").split())
    # Плашка продажу лягає на низ кадру, тому в sell порожнім має бути і він.
    low = (" and the BOTTOM 18% is empty sage paper too" if t["layout"] == "sell"
           else "")
    return (
        BASE + "\n\n"
        "One supplement jar from the attached reference photo: " + jar +
        # Прозорість і капсули описує поле jar: рейші — непрозора біла
        # пляшечка, і «see-through plastic» у спільному шаблоні малював би
        # чужу банку.
        " Reproduce the jar exactly as in the reference: the same shape, "
        "the same white lid, the same material and transparency, the same "
        "label design and colors. The jar is oversized, giant "
        "compared to the person, like in a surreal playful advertising photo. "
        "Do not include the glass stand from the reference photo.\n\n" +
        body + " The jar label faces the camera and nothing covers it.\n\n"
        # 19.10, перша партія: «no taller than half» модель пропускала —
        # у 4 з 12 сцен людина вийшла на зріст банки. Видимий орієнтир
        # (маківка нижче середини банки) тримається краще за пропорцію.
        "SCALE IS THE KEY: the person's whole body, seen full-length, is no "
        "taller than half of the jar's height, like a miniature figure next "
        "to a giant object. The jar is about THREE times taller than the "
        "person. Check it: the top of the person's head is LOWER than the "
        "middle of the jar.\n\n"
        # 19.10, перша проба їжовика: «lid stays closed» модель прочитала
        # як необовʼязкове й намалювала банку взагалі без кришки.
        "Strict rules: there is EXACTLY ONE jar in the whole image — never "
        "two. The jar is closed with its white screw lid on top, exactly as "
        "in the reference — the lid is never missing and never off. Not a "
        "single capsule lies outside the jar — none on the ground, none in "
        "the air.\n\n"
        "Small natural details scattered sparsely around: " +
        # Зайве в кадрі продажу читається як склад: бадьян біля трійчатки,
        # корінь-«женьшень» біля кордицепсу, гриб із шапкою біля рейші.
        details + " Nothing else: no mushroom, plant, root or spice that is "
        "not named in this description.\n\nComposition for a vertical "
        "story: the jar, the person "
        "and the details sit in the middle and lower part of the frame. The "
        "UPPER 38% of the frame is completely empty smooth sage paper with "
        "nothing in it" + low + ".\n\n" +
        TAIL.replace("@LABEL@", " other than the jar label") + NOBRAND)


def esc(s) -> str:
    return (str(s) if s is not None else "").replace("&", "&amp;") \
        .replace("<", "&lt;")


ARROW = ("<svg viewBox='0 0 24 24' fill='none' stroke='#fff' "
         "stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'>"
         "<path d='M5 12h14M13 6l6 6-6 6'/></svg>")

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;position:relative;
 font-family:'Wix Madefor Text';color:@INK@;background:@SAGE@;
 -webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(220,229,210,.94) 0%,rgba(220,229,210,.8) @W1@%,rgba(220,229,210,0) @W2@%)}
.col{position:absolute;left:7.4%;right:7.4%;top:6.4%}
.eye{font-family:Manrope;font-weight:800;font-size:26px;letter-spacing:.08em;
 text-transform:uppercase;color:@OLIVE@;margin-bottom:26px}
h1{font-family:Manrope;font-weight:800;font-size:@H1@px;line-height:1.03;
 letter-spacing:-2.2px}
p{font-weight:500;font-size:@P@px;line-height:1.42;margin-top:30px;
 color:@DIM@;max-width:95%}
.plate{position:absolute;left:6%;right:6%;background:rgba(255,255,255,.95);
 border-radius:38px;box-shadow:0 20px 48px -28px rgba(21,23,26,.5)}
.cta{bottom:5.2%;padding:22px 22px 22px 42px;display:flex;align-items:center;
 justify-content:space-between;gap:24px}
.cta span{font-family:Manrope;font-weight:800;font-size:32px;line-height:1.2}
.go{flex:none;border-radius:50%;background:@OLIVE@;display:flex;
 align-items:center;justify-content:center}
.cta .go{width:92px;height:92px}
.go svg{width:44%;height:44%}
ul{list-style:none;margin-top:40px}
li{display:flex;justify-content:space-between;align-items:baseline;gap:20px;
 font-family:Manrope;font-weight:700;font-size:38px;padding:24px 0;
 border-bottom:2px solid rgba(21,23,26,.1)}
li b{font-weight:800;color:@OLIVE@;white-space:nowrap}
.card{bottom:7.6%;padding:28px 28px 28px 46px;display:grid;
 grid-template-columns:1fr auto auto;align-items:center;gap:30px}
.card.np{grid-template-columns:1fr auto}
.lab{font-family:Manrope;font-weight:800;font-size:26px;letter-spacing:.05em;
 text-transform:uppercase;color:@MUTE@;line-height:1.3}
.nm{font-family:Manrope;font-weight:800;font-size:48px;line-height:1.08;
 margin-top:6px}
.pr{font-family:Manrope;font-weight:800;font-size:58px;text-align:right;
 white-space:nowrap;line-height:1}
.pr.sale{color:@SALE@}
.pr s{display:block;font-size:30px;color:@MUTE@;font-weight:700;margin-top:8px}
.card .go{width:118px;height:118px}
.note{position:absolute;left:0;right:0;bottom:3.6%;text-align:center;
 font-size:28px;font-weight:500;color:@DIM@}
"""


def sizes(claim: str, why: str) -> dict:
    c, n = len(claim or ""), len(why or "")
    h1 = 108 if c <= 22 else 96 if c <= 30 else 86
    p = 40 if n <= 80 else 38 if n <= 130 else 36 if n <= 180 else 34
    return {"@H1@": str(h1), "@P@": str(p)}


def head(t: dict) -> str:
    out = ("<div class='col'><div class='eye'>" + esc(t.get("topic")) +
           "</div><h1>" + esc(t.get("claim")) + "</h1>")
    if t.get("why"):
        out += "<p>" + esc(" ".join(str(t["why"]).split())) + "</p>"
    return out


def render(p: dict, t: dict, bg: Path) -> str:
    lay = t["layout"]
    wash = ("62", "78") if lay == "offer" else ("30", "46")
    body = head(t)

    if lay == "offer":
        rows = ""
        for x in (t.get("extra") or "").split("|"):
            x = " ".join(x.split())
            if not x:
                continue
            name, _, price = x.partition(" — ")
            rows += ("<li><span>" + esc(name) + "</span>" +
                     ("<b>" + esc(price) + "</b>" if price else "") + "</li>")
        body += "<ul>" + rows + "</ul>"
    body += "</div>"

    if lay == "sell":
        price = p.get("price")
        if price:
            cls = "pr sale" if p.get("old") else "pr"
            pr = ("<div class='" + cls + "'>" + esc(price) + " ₴" +
                  ("<s>" + esc(p["old"]) + " ₴</s>" if p.get("old") else "") +
                  "</div>")
        else:
            pr = ""
        body += ("<div class='plate card" + ("" if pr else " np") + "'>"
                 "<div><div class='lab'>" + esc(p.get("plaque")) + "</div>"
                 "<div class='nm'>" + esc(p.get("name")) + "</div></div>" +
                 pr + "<div class='go'>" + ARROW + "</div></div>"
                 "<div class='note'>" + esc(t.get("do")) + "</div>")
    else:
        body += ("<div class='plate cta'><span>" + esc(t.get("do")) +
                 "</span><div class='go'>" + ARROW + "</div></div>")

    css = CSS
    for k, v in sizes(t.get("claim"), t.get("why")).items():
        css = css.replace(k, v)
    for k, v in {"@BG@": data_uri(bg), "@INK@": INK, "@DIM@": DIM,
                 "@MUTE@": MUTE, "@OLIVE@": OLIVE, "@SALE@": SALE,
                 "@SAGE@": SAGE, "@W1@": wash[0], "@W2@": wash[1]}.items():
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
    path = Path(args[0] if args else CONTENT_DIR / "day9_mane.yaml")
    p, items = load(path)
    only = sys.argv[sys.argv.index("--only") + 1].split(",") \
        if "--only" in sys.argv else None

    outdir = OUT_DIR / path.stem
    chk = outdir / "_chk"
    blank = chk / "_blank"
    blank.mkdir(parents=True, exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()

    for t in items:
        if only and t["slot"] not in only:
            continue
        bg = outdir / f"bg_{t['key']}.png"
        if not bg.exists() and tok:
            if t["layout"] in ("giant", "sell"):
                ref = OUT_DIR / "real" / "all" / p["ref"]
                ok = F.draw_ref(giant_prompt(p, t), [ref], tok, bg,
                                aspect="9:16")
            else:
                ok = F.draw_raw(macro_prompt(t), tok, bg, aspect="9:16")
            print(("  ✔ фон " if ok else "  ✖ фон ") + t["key"], flush=True)
        if bg.exists():
            html = render(p, t, bg)
            png = chk / f"{t['key']}.png"
            shot(html, png, w=W, h=H)
            shot(html.replace("</style>",
                              ".col,.plate,.note{visibility:hidden}"
                              "</style>"),
                 blank / f"{t['key']}.png", w=W, h=H)
            Image.open(png).convert("RGB").save(
                outdir / f"{t['key']}.jpg", "JPEG", quality=92)
            print("  ✔ кадр", t["key"], flush=True)

    print("тека:", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
