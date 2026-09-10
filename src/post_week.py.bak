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

URL = "https://lisovik.com.ua/tovar-tyzhnia/"
PAGE = OUT_DIR.parent / "tmp" / "week.html"
DEST = OUT_DIR / "post_week"
W, H = 1080, 1350

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
    return n.strip(" ,")


def caption(items: list) -> str:
    seen, lines = set(), []
    for it in items:
        s = short(it["name"])
        if s in seen:
            continue
        seen.add(s)
        lines.append(f"• {s} — {it['new']} грн замість {it['old']}")
    return (
        "Товар тижня: −20% на добірку для ясної голови\n\n"
        + "\n".join(lines)
        + "\n\nЩо в добірці: їжовик гребінчастий у капсулах і в екстракті, "
          "гінкго білоба та готовий курс, де вони зібрані разом.\n\n"
          "Знижка діє тиждень. Посилання на добірку — в шапці профілю.\n"
          "Питання і замовлення — пиши в директ.\n\n"
          "Дієтична добавка. Не замінює повноцінний раціон харчування. "
          "Не є лікарським засобом.")


def draw(items: list) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    bg = DEST / "bg.png"
    if not bg.exists():
        prompt = (
            "Square-ish 4:5 photograph for a Ukrainian wellness brand. "
            "Several jars and capsule bottles of mushroom and herb powders "
            "standing together in a tight group on a dark surface, seen "
            "slightly from above, "
            "one hard side light carving them out of the dark, deep shadows, "
            "advertising-grade still life. The objects sit low, in the "
            "BOTTOM QUARTER of the frame only; everything above them stays "
            "dark and empty for a headline. "
            "No text, no letters, no labels with readable words, no "
            "watermarks, no red-and-white spotted mushrooms.")
        # Банки в кадрі мусять бути наші, інакше пост рекламує чужий
        # бренд. Дрібний шрифт на етикетках читати не обовʼязково —
        # див. REF_MANY у build_day.
        import build_day as B
        # Рівно ті товари, що в підбірці тижня. Кордицепс тут стояв
        # помилково — його в акції немає, і показувати його означає
        # обіцяти знижку, якої на нього не буде.
        refs = [OUT_DIR / "real" / "all" / n
                for n in ("manecaps.jpg", "mind.jpg", "ginkgo.jpg")]
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

    img = Image.open(bg).convert("RGBA").resize((W, H))
    img = O.fade(img, int(H * 0.78), 225, False, tail=int(H * 0.12))
    d = ImageDraw.Draw(img)

    fk = ST.ImageFont.truetype(ST.FONT_BOLD, int(W * 0.036))
    track = fk.size * 0.16
    label = "ТОВАР ТИЖНЯ"
    wide = sum(d.textlength(c, font=fk) + track for c in label) - track
    x0, y0 = int(W * 0.08), int(H * 0.07)
    d.rectangle([x0 - 14, y0 - 10, x0 + wide + 14, y0 + fk.size + 10],
                fill=O.ACCENT)
    x = x0
    for c in label:
        O.put(d, (x, y0), c, fk, O.INK)
        x += d.textlength(c, font=fk) + track

    fh = ST.ImageFont.truetype(ST.FONT_BOLD, int(W * 0.105))
    y = int(H * 0.135)
    for ln in ST.wrap(d, "−20% НА ЯСНУ ГОЛОВУ", fh, int(W * 0.84)):
        O.put(d, (int(W * 0.08), y), ln, fh, O.WHITE)
        y += int(fh.size * 1.10)

    fp = ST.ImageFont.truetype(ST.FONT_REG, int(W * 0.040))
    y += int(H * 0.018)
    seen = set()
    for it in items:
        s = short(it["name"])
        if s in seen:
            continue
        seen.add(s)
        dot = int(fp.size * 0.30)
        d.ellipse([int(W * 0.08), y + fp.size * 0.42,
                   int(W * 0.08) + dot, y + fp.size * 0.42 + dot],
                  fill=O.ACCENT)
        for i, ln in enumerate(ST.wrap(d, s, fp, int(W * 0.70))):
            O.put(d, (int(W * 0.08) + int(dot * 2.4), y), ln, fp,
                  (238, 238, 240))
            y += int(fp.size * 1.32)
        y += int(H * 0.008)

    img = O.takeaway(img, {"light": False, "fg": O.WHITE},
                     "Посилання в шапці профілю")
    out = DEST / "post_week.jpg"
    img.convert("RGB").save(out, "JPEG", quality=93)
    print("кадр:", out)


def main() -> int:
    if "--fetch" in sys.argv or not PAGE.exists():
        fetch()
    items = products()
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
