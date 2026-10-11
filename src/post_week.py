# -*- coding: utf-8 -*-
"""Пост у стрічку про товар тижня.

Дані зняті зі сторінки lisovik.com.ua/tovar-tyzhnia — назви й обидві ціни,
стара і зі знижкою. Нічого не вигадано: якщо підбірка на сайті зміниться,
скрипт треба перезапустити, а не правити текст руками.

Формат 4:5 — це те, що Instagram показує в стрічці найбільшим.
Дозувань на зображенні немає (бренд-правило), тому «120 шт по 0,4 г»
у кадр не йде: там лише назва й ціна.

    python post_week.py --fetch     # перечитати сторінку
    python post_week.py             # зібрати кадр і підпис
"""
import difflib
import io
import re
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw

import fullgen as F
import generate as gen
import overlays as O
import story_text as ST
from config import OUT_DIR
from render_html import shot, data_uri

# Тема тижня змінюється щотижня, тому заголовок, рядок «що в добірці» і
# референси банок задаються аргументами, а не правкою коду:
#   python post_week.py --fetch --headline "−20% НА ІМУНІТЕТ" \
#          --about "чага, рейші й траметес" --refs chaha_ext,reishi_ext
# Без аргументів лишається поведінка першого тижня («Ясна голова»).
HEADLINE = "−20% НА ЯСНУ ГОЛОВУ"
LEAD = "Товар тижня: −20% на добірку для ясної голови"
ABOUT = ("їжовик гребінчастий у капсулах і в екстракті, гінкго білоба та "
         "готовий курс, де вони зібрані разом")
REFS = ("manecaps.jpg", "mind.jpg", "ginkgo.jpg")
# Дисклеймер залежить від складу підбірки: чай — харчовий продукт,
# і формулювання про дієтичну добавку на нього не поширюється
# (памʼять herbal-teas-niche). Тому він параметр, а не константа.
DISCLAIMER = ("Дієтична добавка. Не замінює повноцінний раціон харчування. "
              "Не є лікарським засобом.")

URL = "https://lisovik.com.ua/tovar-tyzhnia/"
PAGE = OUT_DIR.parent / "tmp" / "week.html"
DEST = OUT_DIR / "post_week"
W, H = 1080, 1350

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?family=Montserrat:"
         "wght@400;500;600;700;800;900&display=swap' rel='stylesheet'>")

# Подачу обрав Ярик 11.10 з восьми проб: світлий камінь, зелена
# типографіка, ціни таблицею — стара перекреслена, нова поруч.
# Попередній стиль (чорне тло, жовта плашка) він забракував цілком.
CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;
 font-family:Montserrat;color:#17351f;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(255,255,255,.96) 0%,rgba(255,255,255,.82) 42%,rgba(255,255,255,0) 62%)}
.col{position:absolute;left:7%;right:7%;top:6%}
.eye{font-weight:700;font-size:20px;letter-spacing:.3em;text-transform:uppercase;
 color:#2f7d45;margin-bottom:16px}
h1{font-weight:800;font-size:92px;line-height:.95;letter-spacing:-3px}
h1 b{color:#2f7d45;font-weight:800}
table{width:100%;margin-top:30px;border-collapse:collapse}
td{padding:11px 0;font-size:29px;vertical-align:baseline;
 border-bottom:1px solid rgba(23,53,31,.14)}
td.n{font-weight:600}
td.o{text-align:right;font-weight:500;font-size:25px;color:#8a9c8f;
 text-decoration:line-through;padding-right:18px;white-space:nowrap}
td.p{text-align:right;font-weight:800;color:#2f7d45;white-space:nowrap}
/* Рядок унизу наїжджав на пакет, і «250Г» з етикетки падало просто в
   нього. Тому під ним власна світла підкладка, як у заголовка. */
.foot{position:absolute;left:0;right:0;bottom:0;height:16%;
 background:linear-gradient(0deg,rgba(255,255,255,.97) 0%,
 rgba(255,255,255,.90) 52%,rgba(255,255,255,0) 100%)}
.do{position:absolute;left:7%;bottom:5%;font-weight:700;font-size:24px;
 letter-spacing:.1em;text-transform:uppercase;
 border-bottom:3px solid #2f7d45;padding-bottom:10px}
"""


def esc(x: str) -> str:
    return (x or "").replace("&", "&amp;").replace("<", "&lt;")


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch() -> None:
    """Сторінка за антиботом: перший запит віддає JS-челендж, у якому
    лежить готовий хеш. Ставимо його кукою і просимо ще раз."""
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-sL", "-A", UA, URL, "-o", str(PAGE)], check=True)
    h = re.search(r'"([a-f0-9]{64})"', PAGE.read_text(encoding="utf-8",
                                                      errors="replace"))
    if h:
        subprocess.run(["curl", "-sL", "-A", UA, "-b",
                        f"challenge_passed={h.group(1)}", URL,
                        "-o", str(PAGE)], check=True)
    print(f"сторінку збережено: {PAGE.stat().st_size // 1024} КБ")


def products() -> list:
    """Назви й пари цін зі сторінки підбірки."""
    h = PAGE.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", "|", h))
    parts = [re.sub(r"\s+", " ", x).strip() for x in txt.split("|")]
    parts = [p for p in parts if p]
    out = []
    for i, p in enumerate(parts):
        if not re.fullmatch(r"[\d\s]{3,8}грн", p):
            continue
        if i + 1 >= len(parts) or not re.fullmatch(r"[\d\s]{3,8}грн",
                                                   parts[i + 1]):
            continue
        name = ""
        for j in range(i - 1, max(0, i - 8), -1):
            if len(parts[j]) > 12 and not parts[j].replace(" ", "").isdigit():
                name = parts[j]
                break
        if name:
            out.append({"name": name,
                        "old": p.replace("грн", "").strip(),
                        "new": parts[i + 1].replace("грн", "").strip()})
    return out


def short(name: str) -> str:
    """Назва для кадру: без фасовок і дозувань — їх на зображення не
    можна, і вони ж роблять рядок нечитабельним."""
    n = re.split(r",|\s+\d+\s*(шт|капсул)", name)[0]
    n = re.sub(r"\s*\([^)]*\)", "", n)          # «(1 місяць)» — це фасовка
    n = re.sub(r"\s+для розумової активності", "", n)
    n = re.sub(r"^Гриби?\s+", "", n)            # «Гриб Траметес» = «Траметес»
    # Фасовка в кадр не йде: вона є в підписі, а на зображенні через неї
    # одна спіруліна дає шість рядків замість двох і список лізе за край.
    n = re.sub(r"\s+\d+\s*[+]\s*\d+\s*г", "", n)   # «100+100 г»
    n = re.sub(r"\s+\d+\s*г", "", n)                 # «250 г»
    # «WOMEN Natural Power Formula» — найдовший рядок списку, він наповзав
    # на кришки банок (27.09). На банері цей самий товар — «комплекс WOMEN».
    n = re.sub(r"^(WOMEN|MEN) Natural Power Formula$", r"Комплекс \1", n)
    n = n.split("/")[0]                         # «Рейші/Трутовик лакований»
    if n.startswith("Курс"):
        n = n.split(":")[0]                     # «Курс Immunity Guard: ...»
    return n.strip(" ,")


def group(items: list) -> list:
    """Одна карточка = один рядок, ціна найдешевшої фасовки."""
    out = {}
    for it in items:
        key = short(it["name"])
        cost = int(re.sub(r"\D", "", it["new"]) or 0)
        if key not in out or cost < out[key]["cost"]:
            out[key] = {"name": key, "old": it["old"], "new": it["new"],
                        "cost": cost}
    return list(out.values())


def caption(items: list) -> str:
    lines = []
    for it in group(items):
        lines.append(f"• {it['name']} — від {it['new']} грн замість {it['old']}")
    return (
        LEAD + "\n\n"
        + "\n".join(lines)
        + "\n\nЩо в добірці: " + ABOUT + ".\n\n"
          "Знижка діє тиждень. Посилання на добірку — в шапці профілю.\n"
          "Питання і замовлення — пиши в директ.\n\n"
        + DISCLAIMER)


def draw(items: list) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    bg = DEST / "bg.png"
    if not bg.exists():
        prompt = (
            "FLAT LAY, camera directly overhead, soft daylight on a pale "
            "stone surface: two of the attached packages lying flat in the "
            "BOTTOM HALF of the frame beside a wooden spoon heaped with "
            "bright green powder and a small loose scatter of the same "
            "powder. The TOP HALF is bare pale stone, completely empty. "
            "Draw ONLY the kinds of package shown in the attached photos — "
            "if they are stand-up pouches, every package in the frame is a "
            "pouch: no jars, no bottles, no tins invented on top of them. "
            "NO text of your own anywhere in the image, no watermarks, no "
            "red-and-white spotted mushrooms.")
        # Банки в кадрі мусять бути наші, інакше пост рекламує чужий
        # бренд. Дрібний шрифт на етикетках читати не обовʼязково —
        # див. REF_MANY у build_day.
        import build_day as B
        # Рівно ті товари, що в підбірці тижня. Кордицепс тут стояв
        # помилково — його в акції немає, і показувати його означає
        # обіцяти знижку, якої на нього не буде.
        refs = [OUT_DIR / "real" / "all" / n for n in REFS]
        full = prompt + " " + " ".join(B.REF_MANY.split())
        import verify_frame as V
        tok = gen.token()
        for n in range(1, 5):
            if not F.draw_ref(full, refs, tok, bg, aspect="4:5"):
                continue
            # Пост у стрічці дивляться крупно, тому одруківка на етикетці
            # тут помітна — на відміну від сторіс. Ганяємо ту саму
            # перевірку на спотворене своє слово.
            seen = V.check(bg, [], tok).get("seen", {})
            words = " ".join(seen.get("text_lines", [])).lower()
            bad = [w for w in re.findall(r"[а-яіїєґ]{5,}", words)
                   if difflib.get_close_matches(w, B.EXACT_LABEL, 1, 0.80)
                   and w not in B.EXACT_LABEL]
            if not bad:
                break
            print(f"  ~ спотворене слово: {', '.join(bad[:3])}")
            bg.unlink(missing_ok=True)
        if not bg.exists():
            print("тло не намалювалось")
            return

    # Верстка через HTML: у PIL перекреслена ціна коштувала б окремої
    # лінії під кожним рядком, а тут це одна властивість тексту.
    rows = "".join(
        "<tr><td class='n'>" + esc(it["name"]) + "</td>"
        "<td class='o'>" + it["old"] + "</td>"
        "<td class='p'>" + it["new"] + " грн</td></tr>"
        for it in group(items))
    html = ("<html><head>" + FONTS + "<style>" +
            CSS.replace("@BG@", data_uri(bg)) + "</style></head><body>"
            "<div class='bg'></div><div class='wash'></div>"
            "<div class='col'><div class='eye'>Товар тижня</div>"
            "<h1>" + HEADLINE + "</h1>"
            "<table>" + rows + "</table></div>"
            "<div class='foot'></div>"
            "<div class='do'>Посилання в шапці профілю</div></body></html>")
    out = DEST / "post_week.jpg"
    shot(html, out, w=W, h=H)
    print("кадр:", out)


def arg(name: str, default):
    """--name значення; повертає default, якщо прапорця немає."""
    key = "--" + name
    if key in sys.argv:
        i = sys.argv.index(key)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main() -> int:
    global HEADLINE, LEAD, ABOUT, REFS, DISCLAIMER
    HEADLINE = arg("headline", HEADLINE)
    LEAD = arg("lead", LEAD)
    ABOUT = arg("about", ABOUT)
    DISCLAIMER = arg("disclaimer", DISCLAIMER)
    refs = arg("refs", None)
    if refs:
        REFS = tuple((x if x.endswith(".jpg") else x + ".jpg")
                     for x in refs.split(","))
    if "--fetch" in sys.argv or not PAGE.exists():
        fetch()
    items = products()
    # Підбірка на сайті і підбірка в пості — не завжди одне й те саме.
    # Мухомор стоїть у розділі, але в стрічку Meta його нести не можна:
    # Amanita muscaria під забороною «Drugs and drug-related products»,
    # а санкція там акаунтна — ляже весь фід разом із курсами.
    skip = arg("skip", "")
    if skip:
        pats = [x.strip().lower() for x in skip.split(",") if x.strip()]
        keep = [it for it in items if not any(p in it["name"].lower() for p in pats)]
        print("прибрано з поста: %d позицій за «%s»" % (len(items) - len(keep), skip))
        items = keep
    if not items:
        print("товарів на сторінці не знайдено")
        return 1
    print(f"товарів у добірці: {len(items)}")
    for it in items:
        print(f"   {short(it['name'])[:52]:54} {it['old']:>7} → {it['new']}")
    DEST.mkdir(parents=True, exist_ok=True)
    text = caption(items)
    io.open(DEST / "caption.txt", "w", encoding="utf-8").write(text)
    print("\n" + textwrap.indent(text, "   "))
    draw(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
