# -*- coding: utf-8 -*-
"""Карусель у стрічку: магній гліцинат, вісім кадрів.

Вайб «синя лабораторія» обрав Ярик 29.09 з трьох проб: глибокий синій
під колір етикетки, біла типографіка, число на пів кадру. Пост тримається
на одній думці з картки — на банках пишуть вагу сполуки, а рахувати треба
елементарний магній.

Правило власника: ПРОДУКТ НА ПЕРШОМУ КАДРІ.

  1 обкладинка  банка, 104 мг, ціна дня
  2 проблема    велика цифра на банці — це вага сполуки
  3 цифра       104 мг у капсулі, 208 на добу, 55% норми
  4 форми       оксид / цитрат / бісгліцинат
  5 хелат       мінерал, зв'язаний із двома молекулами гліцину
  6 схема       одна вранці, одна ввечері
  7 офіційно    дозволені формулювання європейського реєстру
  8 фінал       дві фасовки й ціни

Кадри 2, 4, 5 і 7 — суцільний синій без фото: у каруселі з восьми
екранів суцільне предметне фото втомлює швидше, ніж чистий колір.

Дозування тут дозволені: заборона на них — правило сторіс, а весь сенс
цього поста саме в цифрі.

    python build_post_mg.py            # згенерувати й зібрати
    python build_post_mg.py --compose  # тільки перезібрати з наявних фонів
"""
import sys
from pathlib import Path

from PIL import Image

import build_day as B
import fullgen as F
import generate as gen
from config import OUT_DIR
from render_html import shot, data_uri

OUT = OUT_DIR / "post_mg"
REFS = [OUT_DIR / "real" / "all" / "magnium.jpg"]
W, H = 1080, 1350

KEEP = (" The product is a WHITE OPAQUE plastic bottle with a WHITE screw lid, "
        "wrapped around its middle with a DEEP NAVY BLUE paper label that "
        "carries the white ЛІСОВИК tree-face logo and the words МАГНІЙ "
        "ГЛІЦИНАТ. The bottle itself is WHITE plastic: the lid, the neck, the "
        "shoulders and the bottom rim stay plain white, exactly as in the "
        "attached photo. It is not transparent and not blue all over.")
TAIL = (" NO TEXT anywhere in the image except the wording printed on the "
        "product label. No stamps, seals or badges in the background.")
NAVY = ("Editorial product photograph on a seamless DEEP NAVY BLUE background, "
        "one soft light from the upper left, gentle shadow. ")

# Кадри без фото: фон малюється градієнтом, генерація не потрібна.
SCENES = {
 "k1": (NAVY + "The bottle from the attached photo stands alone and VERY "
        "SMALL — barely a fifth of the frame height — low in the frame, seen "
        "straight on. Its white lid is WHOLE and sits BELOW the three-quarter "
        "line, so the TOP THREE QUARTERS are plain empty navy blue with "
        "nothing in them at all, and there is empty navy blue below the bottle "
        "too. There is EXACTLY ONE bottle in the frame." + KEEP + TAIL),
 "k3": (NAVY + "About eight pale ivory capsules lie scattered in a loose group "
        "on the surface, entirely inside the BOTTOM QUARTER of the frame, "
        "sharp and detailed. There is NO bottle, NO jar, NO box and NO "
        "packaging of any kind in this image — only loose capsules on a plain "
        "surface. The TOP THREE QUARTERS of the frame are plain empty navy "
        "blue, nothing in them at all." + TAIL),
 "k6": (NAVY + "The bottle from the attached photo stands alone and VERY "
        "SMALL — barely a fifth of the frame height — low and left of centre, "
        "with exactly TWO pale ivory capsules lying on the surface to its "
        "right. Its white lid is WHOLE and sits BELOW the three-quarter line "
        "of the frame, so the TOP THREE QUARTERS are plain empty navy blue "
        "with nothing in them at all. There is EXACTLY ONE bottle in the "
        "frame." + KEEP + TAIL),
 "k8": (NAVY + "The bottle from the attached photo stands alone and VERY "
        "SMALL — barely a fifth of the frame height — low and slightly right "
        "of centre, seen slightly from the side, one long soft shadow to the "
        "left. Its white lid is WHOLE and sits BELOW the three-quarter line, "
        "so the TOP THREE QUARTERS are plain empty navy blue with nothing in "
        "them at all. There is EXACTLY ONE bottle in the frame." + KEEP + TAIL),
}

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?family=Montserrat:"
         "wght@400;500;600;700;800;900&display=swap' rel='stylesheet'>")

# Градієнт повторює світло згенерованих кадрів, щоб гортання не стрибало.
PLAIN = ("radial-gradient(120% 90% at 26% 18%,#25457d 0%,#1b3663 42%,"
         "#12244a 100%)")

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;
 font-family:Montserrat;color:#eef3fb;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:@BG@}
.col{position:absolute;left:8%;right:8%;top:6%}
.mid .col{top:50%;transform:translateY(-50%)}
.eye{font-weight:700;font-size:24px;letter-spacing:.3em;text-transform:uppercase;
 color:#8fb3e0;margin-bottom:26px}
.num{font-weight:900;font-size:300px;line-height:.78;letter-spacing:-14px;
 color:#fff}
.num i{font-style:normal;font-weight:800;font-size:76px;letter-spacing:0;
 margin-left:14px}
h1{font-weight:800;font-size:@H1@px;line-height:.98;letter-spacing:-2px;
 text-transform:uppercase}
p{font-weight:500;font-size:@P@px;line-height:1.36;margin-top:24px;
 max-width:86%;color:rgba(238,243,251,.82)}
ul{list-style:none;margin-top:30px}
li{font-weight:600;font-size:33px;line-height:1.28;padding:20px 0;
 border-bottom:1px solid rgba(143,179,224,.3);color:#dce7f7}
li b{font-weight:800;color:#fff}
.do{position:absolute;left:8%;bottom:6%;font-weight:800;font-size:30px;
 letter-spacing:.06em;text-transform:uppercase;color:#12244a;
 background:#9fc4f0;padding:18px 26px;border-radius:4px}
.pg{position:absolute;right:8%;bottom:7.5%;font-weight:700;font-size:26px;
 letter-spacing:.2em;color:#7ea3d6}
"""

CARDS = [
 dict(key="k1", eye="Магній гліцинат", num="104", unit="мг",
      h1="у капсулі, а не вага солі",
      p="На банках пишуть вагу сполуки. Рахувати ж треба елементарний "
        "магній — той, що справді дійде до тебе.",
      do="від 16 грн на день", h1size=62, psize=30),
 dict(key="k2", eye="Як читають банку", h1="Велика цифра — не про магній",
      p="«600 мг магнію бісгліцинату» — це вага всієї сполуки. Самого "
        "мінералу в ній лише частина, і яка саме, банка часто не каже.",
      h1size=88, psize=34),
 dict(key="k3", eye="Скільки насправді", h1="104 мг у капсулі, 208 на добу",
      p="Це елементарний магній — той, за яким рахують норму. Дві капсули "
        "закривають 55% референсних 375 мг, решту добирає їжа.",
      h1size=80, psize=33),
 dict(key="k4", eye="Три форми магнію", h1="Чому бісгліцинат",
      items=["<b>Оксид</b> — найбільше магнію на грам, найгірше переноситься",
             "<b>Цитрат</b> — помітно послаблює",
             "<b>Бісгліцинат</b> — хелат, найм'якший для шлунка"],
      p="До третьої форми приходять тоді, коли перші дві не підійшли.",
      h1size=92, psize=31),
 dict(key="k5", eye="Що таке хелат", h1="Мінерал, загорнутий у гліцин",
      p="У хелаті магній зв'язаний із двома молекулами амінокислоти гліцину. "
        "Це друга половина сполуки — і саме через неї форму традиційно "
        "ставлять у вечірній прийом.",
      h1size=80, psize=33),
 dict(key="k6", eye="Схема", h1="Одна вранці, одна ввечері",
      p="Капсули однакові, рахувати нічого не треба. Вечірню зазвичай беруть "
        "ближче до сну. Банка 60 шт — це 30 днів, 120 шт — 60.",
      h1size=84, psize=33),
 dict(key="k7", eye="Офіційно", h1="Це не наші слова",
      items=["зменшення втоми та виснаження",
             "нормальна робота нервової системи",
             "нормальна робота м'язів",
             "нормальний психологічний стан"],
      p="Формулювання з європейського реєстру. Право на них дає вміст від "
        "15% норми — у нас 55%.",
      h1size=92, psize=30),
 dict(key="k8", eye="Дві фасовки", h1="60 або 120 капсул",
      p="590 грн на місяць, 985 на два — від 16 грн на день. Оболонка "
        "капсули рослинна, без желатину.",
      do="Посилання в шапці профілю", h1size=92, psize=33),
]


def esc(s):
    return (s or "").replace("&", "&amp;")


def render(c: dict, bg: Path, n: int) -> str:
    css = (CSS.replace("@H1@", str(c["h1size"]))
              .replace("@P@", str(c["psize"]))
              .replace("@BG@", f"url('{data_uri(bg)}') center/cover"
                       if bg else PLAIN))
    if c.get("num"):
        head = ("<div class='num'>" + c["num"] + "<i>" + c["unit"] +
                "</i></div><h1>" + esc(c["h1"]) + "</h1>")
    else:
        head = "<h1>" + esc(c["h1"]) + "</h1>"
    rows = ("<ul>" + "".join("<li>" + x + "</li>" for x in c["items"]) + "</ul>"
            if c.get("items") else "")
    body = ("<div class='col'><div class='eye'>" + esc(c["eye"]) + "</div>" +
            head + rows + "<p>" + esc(c["p"]) + "</p></div>")
    do = "<div class='do'>" + esc(c["do"]) + "</div>" if c.get("do") else ""
    pg = f"<div class='pg'>{n} / {len(CARDS)}</div>"
    cls = "" if bg else " class='mid'"
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head>"
            "<body" + cls + "><div class='bg'></div>" + body + do + pg +
            "</body></html>")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_blank").mkdir(exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()

    for n, c in enumerate(CARDS, 1):
        bg = OUT / f"bg_{c['key']}.png"
        scene = SCENES.get(c["key"])
        if scene and not bg.exists() and tok:
            ok = F.draw_ref(scene + " " + " ".join(B.REF_MANY.split()),
                            REFS, tok, bg, aspect="4:5")
            print(("  ✔ фон " if ok else "  ✖ фон ") + c["key"], flush=True)
        use = bg if (scene and bg.exists()) else None
        html = render(c, use, n)
        png = OUT / f"{n}_{c['key']}.png"
        shot(html, png, w=W, h=H)
        shot(html.replace("</style>",
                          ".col,.col *,.do,.pg{color:transparent!important}"
                          "</style>"),
             OUT / "_blank" / f"{n}_{c['key']}.png", w=W, h=H)
        Image.open(png).convert("RGB").save(
            OUT / f"{n}_{c['key']}.jpg", "JPEG", quality=92)
        print("  ✔ кадр", n, c["key"], flush=True)

    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
