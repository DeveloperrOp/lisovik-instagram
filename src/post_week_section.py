# -*- coding: utf-8 -*-
"""Пост у стрічку про розділ «Товар тижня» — без товарів.

25.10.2026 добірка тижня на сайті цілком складалась із мухомора й
«мікродозингу». У стрічку це не йде ніколи (Entheogens, бан BM), а
вирізати безпечну частину не було з чого. Ярик: «надо как-то аккуратно и
указать, что раздел на сайте в шапке профиля».

Тому пост вічнозелений: про те, як працює розділ, а не що в ньому зараз.
Без банок (чужий товар на кадрі = обман про знижку) і без грибів узагалі.
Стиль — «гербарій на шалфеї» тижня 10.

Кладе кадр і підпис у out/post_week/, звідки публікує publish_post_week.py.

    python post_week_section.py
"""
import io
import sys

import fullgen as F
import generate as gen
from build_story_v8 import TAIL
from config import OUT_DIR
from render_html import shot, data_uri

DEST = OUT_DIR / "post_week"
W, H = 1080, 1350

PROMPT = (
    "Vintage herbarium sheet photographed flat from directly above, on "
    "smooth light sage-green matte paper (#DCE5D2), soft even daylight, calm "
    "and clean, everything tack-sharp. In the LOWER HALF, sparsely arranged: "
    "three BLANK cream specimen tags tied with twine, one blank glassine "
    "envelope, a few strips of paper tape and three small pressed dry oak "
    "leaves. The UPPER 52% of the frame is bare sage paper, completely "
    "empty. NO mushrooms of any kind, no berries, no red objects, no jars, "
    "no bottles, no packages." + TAIL)

# Слова зі сторінки розділу: «Спецпропозиція показана прямо в плитці
# товару… Промокод вводити не треба». «Приблизно щотижня» з тієї ж
# сторінки Ярик поправив 25.10: добірку міняють раз на тиждень.
CAPTION = (
    "Товар тижня — розділ на нашому сайті зі знижкою на добірку.\n\n"
    "Добірку міняємо раз на тиждень: одні позиції повертаються до звичайної "
    "ціни, на їхнє місце стають інші. Акційна ціна вже стоїть у картці "
    "товару — промокод вводити не треба.\n\n"
    "Що в добірці цього тижня — дивись у розділі «Товар тижня». Посилання "
    "на сайт — у шапці профілю.\n"
    "Питання — пиши в директ.")

FONTS = ("<link href='https://fonts.googleapis.com/css2?family=Manrope:wght@700;800"
         "&family=Wix+Madefor+Text:wght@500&display=swap' rel='stylesheet'>")

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;
 font-family:'Wix Madefor Text';color:#15171A;background:#DCE5D2}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(220,229,210,.93),rgba(220,229,210,.7) 40%,rgba(220,229,210,0) 56%)}
.col{position:absolute;left:8%;right:8%;top:8%}
.eye{font-family:Manrope;font-weight:800;font-size:26px;letter-spacing:.12em;
 text-transform:uppercase;color:#5A8326}
h1{font-family:Manrope;font-weight:800;font-size:96px;line-height:1.02;
 letter-spacing:-2.4px;margin-top:22px}
p{font-weight:500;font-size:36px;line-height:1.4;margin-top:26px;color:#3B4148}
.lab{position:absolute;left:8%;bottom:7%;background:#FBF8EF;
 border:2px solid #2b2d24;padding:22px 30px;transform:rotate(-1.2deg);
 box-shadow:0 12px 26px -16px rgba(30,34,20,.45);font-family:Manrope;
 font-weight:800;font-size:30px}
.lab:before,.lab:after{content:'';position:absolute;width:100px;height:30px;
 background:rgba(236,226,200,.8);top:-15px}
.lab:before{left:-24px;transform:rotate(-24deg)}
.lab:after{right:-24px;transform:rotate(22deg)}
.lab b{color:#5A8326}
"""


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    bg = DEST / "bg.png"
    if not bg.exists():
        ok = F.draw_raw(PROMPT, gen.token(), bg, aspect="4:5")
        print(("✔ тло" if ok else "✖ тло"), flush=True)
        if not ok:
            return 1
    html = ("<html><head>" + FONTS + "<style>" + CSS.replace("@BG@", data_uri(bg))
            + "</style></head><body><div class='bg'></div><div class='wash'></div>"
            "<div class='col'><div class='eye'>Товар тижня</div>"
            "<h1>Щотижня — нова добірка зі знижкою</h1>"
            "<p>Що в ній цього тижня —<br>у розділі «Товар тижня» на сайті.</p></div>"
            "<div class='lab'>Посилання на сайт — у шапці профілю <b>→</b></div>"
            "</body></html>")
    out = DEST / "post_week.jpg"
    shot(html, out, w=W, h=H, wait=1800)
    io.open(DEST / "caption.txt", "w", encoding="utf-8").write(CAPTION)
    print("кадр:", out)
    print("\n" + CAPTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
