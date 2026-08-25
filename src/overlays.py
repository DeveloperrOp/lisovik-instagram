# -*- coding: utf-8 -*-
"""Забор текстовых раскладок: двенадцать способов подать текст на кадре.

Одна фраза на плашке — это один приём, а не выбор. Здесь варианты:
списки, шаги с номерами, две колонки, крупная цифра, выноска со стрелкой,
карточка, ленты, шкала.

Весь текст и вся графика рисуются PIL. Модели тут не доверяем ничего:
у неё на длинной фразе ломается орфография, а вычитать её нечем.
Зато PIL даёт точность до пикселя и любые элементы без риска.

    python overlays.py --list
    python overlays.py --all          # лист сравнения на светлом и тёмном
"""
import sys

from PIL import Image, ImageDraw

import story_text as ST
from config import OUT_DIR

OUTDIR = OUT_DIR / "overlays"

WHITE = (255, 255, 255)
INK = (20, 20, 22)
ACCENT = (255, 199, 44)
DIMMED = (196, 198, 200)


def scheme(img, pos=0.08, span=0.55):
    """Тёмный кадр или светлый — от этого зависит вся палитра слоя."""
    light = ST.brightness(img, pos, pos + span) > 140
    return {
        "light": light,
        "fg": INK if light else WHITE,
        "sub": (78, 78, 82) if light else DIMMED,
        "panel": (252, 250, 246) if light else (16, 16, 18),
        "line": (0, 0, 0, 40) if light else (255, 255, 255, 46),
    }


def veil(img, top, height, strength=150, light=False):
    """Полупрозрачная подложка под блоком текста, без резких краёв."""
    W, H = img.size
    rgb = (250, 248, 244) if light else (12, 12, 14)
    layer = Image.new("RGBA", (W, int(H * height)), rgb + (strength,))
    img.alpha_composite(layer, (0, int(H * top)))
    return img


def fnt(img, k, bold=True):
    return ST.ImageFont.truetype(ST.FONT_BOLD if bold else ST.FONT_REG,
                                 max(14, int(img.width * k)))


def head(d, img, s, text, k=0.058, x=0.08, y=0.085, gap=1.16):
    """Заголовок с переносом. Без него длинная строка уезжала за край кадра."""
    W, H = img.size
    f = fnt(img, k)
    yy = int(H * y)
    for ln in ST.wrap(d, text, f, int(W * (0.92 - x))):
        put(d, (int(W * x), yy), ln, f, s["fg"])
        yy += int(f.size * gap)
    return yy


def put(d, xy, text, f, fill, anchor="la"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


# ------------------------------------------------------------- раскладки

def line(img, s, data):
    """Одна фраза на плашке — то, с чего начинали."""
    return ST.draw(img, data["headline"], kind="box", pos=0.30)


def title_sub(img, s, data):
    """Три уровня: заголовок, пояснение, вывод внизу."""
    W, H = img.size
    img = veil(img, 0.06, 0.34, 130, s["light"])
    d = ImageDraw.Draw(img)
    fh, fb = fnt(img, 0.072), fnt(img, 0.037, False)
    y = int(H * 0.10)
    for ln in ST.wrap(d, data["headline"], fh, int(W * 0.84)):
        put(d, (int(W * 0.08), y), ln, fh, s["fg"])
        y += int(fh.size * 1.16)
    y += int(H * 0.012)
    for ln in ST.wrap(d, data["body"], fb, int(W * 0.82)):
        put(d, (int(W * 0.08), y), ln, fb, s["sub"])
        y += int(fb.size * 1.42)
    return img


def steps(img, s, data):
    """Нумерованные шаги: цифра в кружке, текст рядом."""
    W, H = img.size
    img = veil(img, 0.05, 0.42, 145, s["light"])
    d = ImageDraw.Draw(img)
    ft, fn_ = fnt(img, 0.040, False), fnt(img, 0.034)
    y = head(d, img, s, data["headline"], 0.058) + int(H * 0.02)
    r = int(W * 0.038)
    for i, step in enumerate(data["steps"], 1):
        cx, cy = int(W * 0.11), y + r
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT)
        put(d, (cx, cy), str(i), fn_, INK, anchor="mm")
        put(d, (int(W * 0.18), cy), step, ft, s["fg"], anchor="lm")
        y += int(H * 0.072)
    return img


def bullets(img, s, data):
    """Список: маркер-квадратик и строка."""
    W, H = img.size
    img = veil(img, 0.05, 0.40, 145, s["light"])
    d = ImageDraw.Draw(img)
    ft = fnt(img, 0.038, False)
    y = head(d, img, s, data["headline"], 0.058) + int(H * 0.018)
    for item in data["points"]:
        b = int(W * 0.016)
        d.rectangle((int(W * 0.085), y + b, int(W * 0.085) + b, y + 2 * b),
                    fill=ACCENT)
        put(d, (int(W * 0.14), y), item, ft, s["fg"])
        y += int(ft.size * 1.75)
    return img


def versus(img, s, data):
    """Две колонки с вертикальным разделителем."""
    W, H = img.size
    img = veil(img, 0.06, 0.40, 150, s["light"])
    d = ImageDraw.Draw(img)
    fh, fc, ft = fnt(img, 0.050), fnt(img, 0.044), fnt(img, 0.031, False)
    y = int(H * 0.09)
    for ln in ST.wrap(d, data["headline"], fh, int(W * 0.86)):
        put(d, (W // 2, y), ln, fh, s["fg"], anchor="ma")
        y += int(fh.size * 1.14)
    top, bot = y + int(H * 0.02), int(H * 0.45)
    d.line([(W // 2, top), (W // 2, bot)], fill=s["line"][:3], width=2)
    for side, col in enumerate(data["columns"]):
        cx = int(W * (0.27 if side == 0 else 0.73))
        put(d, (cx, top), col["title"], fc, ACCENT, anchor="ma")
        y = top + int(fc.size * 1.7)
        for p in col["points"]:
            for ln in ST.wrap(d, p, ft, int(W * 0.38)):
                put(d, (cx, y), ln, ft, s["fg"], anchor="ma")
                y += int(ft.size * 1.32)
            y += int(ft.size * 0.35)
    return img


def stat(img, s, data):
    """Крупная цифра как главный герой, пояснение под ней."""
    W, H = img.size
    img = veil(img, 0.06, 0.34, 140, s["light"])
    d = ImageDraw.Draw(img)
    fbig, ft = fnt(img, 0.20), fnt(img, 0.038, False)
    y0 = int(H * 0.075)
    put(d, (W // 2, y0), data["stat"], fbig, ACCENT, anchor="ma")
    # подпись ставим ПОД цифрой: раньше она шла вровень и налезала сбоку
    y = y0 + int(fbig.size * 1.12)
    for ln in ST.wrap(d, data["stat_note"], ft, int(W * 0.78)):
        put(d, (W // 2, y), ln, ft, s["fg"], anchor="ma")
        y += int(ft.size * 1.35)
    return img


def quote(img, s, data):
    """Выделенная мысль с крупной кавычкой."""
    W, H = img.size
    img = veil(img, 0.16, 0.30, 150, s["light"])
    d = ImageDraw.Draw(img)
    fq, ft = fnt(img, 0.17), fnt(img, 0.050, False)
    put(d, (int(W * 0.09), int(H * 0.15)), "«", fq, ACCENT)
    y = int(H * 0.235)
    for ln in ST.wrap(d, data["quote"], ft, int(W * 0.78)):
        put(d, (int(W * 0.11), y), ln, ft, s["fg"])
        y += int(ft.size * 1.34)
    return img


def card(img, s, data):
    """Карточка внизу: заголовок и абзац на сплошной подложке."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    fh, ft = fnt(img, 0.056), fnt(img, 0.034, False)
    lines = ST.wrap(d, data["body"], ft, int(W * 0.80))
    hlines = ST.wrap(d, data["headline"], fh, int(W * 0.78))
    h = int(len(hlines) * fh.size * 1.28 + len(lines) * ft.size * 1.42
            + H * 0.05)
    top = H - h - int(H * 0.11)
    panel = Image.new("RGBA", (int(W * 0.88), h), s["panel"] + (232,))
    img.alpha_composite(panel, (int(W * 0.06), top))
    d = ImageDraw.Draw(img)
    fg = INK if s["light"] else WHITE
    y = top + int(H * 0.022)
    for ln in hlines:
        put(d, (int(W * 0.10), y), ln, fh, fg)
        y += int(fh.size * 1.28)
    y += int(fh.size * 0.25)
    for ln in lines:
        put(d, (int(W * 0.10), y), ln, ft, (90, 90, 94) if s["light"] else DIMMED)
        y += int(ft.size * 1.42)
    return img


def bands(img, s, data):
    """Две ленты: тема сверху, вывод снизу. Как титры."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    ft, fb = fnt(img, 0.032), fnt(img, 0.046)
    h1 = int(ft.size * 2.2)
    img.alpha_composite(Image.new("RGBA", (W, h1), ACCENT + (255,)),
                        (0, int(H * 0.07)))
    d = ImageDraw.Draw(img)
    put(d, (W // 2, int(H * 0.07) + h1 // 2), data["kicker"].upper(), ft,
        INK, anchor="mm")
    lines = ST.wrap(d, data["headline"], fb, int(W * 0.86))
    h2 = int(len(lines) * fb.size * 1.3 + fb.size)
    top = H - h2 - int(H * 0.10)
    img.alpha_composite(Image.new("RGBA", (W, h2), (14, 14, 16, 225)), (0, top))
    d = ImageDraw.Draw(img)
    y = top + int(fb.size * 0.45)
    for ln in lines:
        put(d, (W // 2, y), ln, fb, WHITE, anchor="ma")
        y += int(fb.size * 1.3)
    return img


def callout(img, s, data):
    """Выноска со стрелкой к объекту — как подпись на схеме."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    ft = fnt(img, 0.034, False)
    lines = ST.wrap(d, data["callout"], ft, int(W * 0.42))
    bw = int(W * 0.50)
    bh = int(len(lines) * ft.size * 1.35 + ft.size * 0.9)
    bx, by = int(W * 0.07), int(H * 0.20)
    panel = Image.new("RGBA", (bw, bh), (250, 248, 244, 240))
    img.alpha_composite(panel, (bx, by))
    d = ImageDraw.Draw(img)
    y = by + int(ft.size * 0.45)
    for ln in lines:
        put(d, (bx + int(W * 0.035), y), ln, ft, INK)
        y += int(ft.size * 1.35)
    # линия-указатель уходит к центру кадра, где стоит предмет
    ex, ey = int(W * 0.62), int(H * 0.52)
    d.line([(bx + bw, by + bh // 2), (ex, ey)], fill=ACCENT, width=4)
    r = int(W * 0.014)
    d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=ACCENT)
    return img


def underline(img, s, data):
    """Заголовок с акцентной чертой под ключевым словом."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    fh = fnt(img, 0.078)
    lines = ST.wrap(d, data["headline"], fh, int(W * 0.84))
    y = int(H * 0.10)
    img = veil(img, 0.06, 0.26, 120, s["light"])
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        put(d, (int(W * 0.08), y), ln, fh, s["fg"])
        if i == len(lines) - 1:
            w = d.textlength(ln, font=fh)
            # раньше черта проходила сквозь текст: у шрифта высота строки
            # больше кегля, и множителя 1.06 не хватало
            yy = y + int(fh.size * 1.28)
            d.line([(int(W * 0.08), yy), (int(W * 0.08) + w, yy)],
                   fill=ACCENT, width=max(4, int(W * 0.008)))
        y += int(fh.size * 1.18)
    return img


def scale(img, s, data):
    """Шкала со значением — когда речь о температуре или дозе."""
    W, H = img.size
    img = veil(img, 0.06, 0.32, 145, s["light"])
    d = ImageDraw.Draw(img)
    fv, ft = fnt(img, 0.085), fnt(img, 0.028, False)
    hy = head(d, img, s, data["headline"], 0.048)
    x0, x1 = int(W * 0.08), int(W * 0.92)
    y = hy + int(H * 0.075)
    d.rounded_rectangle((x0, y, x1, y + int(H * 0.012)),
                        radius=int(H * 0.006), fill=s["line"][:3])
    a, b = data["range"]
    xa, xb = x0 + int((x1 - x0) * a), x0 + int((x1 - x0) * b)
    d.rounded_rectangle((xa, y, xb, y + int(H * 0.012)),
                        radius=int(H * 0.006), fill=ACCENT)
    put(d, ((xa + xb) // 2, y - int(H * 0.014)), data["value"], fv,
        s["fg"], anchor="md")
    put(d, (x0, y + int(H * 0.026)), data["scale_lo"], ft, s["sub"])
    put(d, (x1, y + int(H * 0.026)), data["scale_hi"], ft, s["sub"], anchor="ra")
    return img


def qa(img, s, data):
    """Вопрос сверху, ответ на плашке снизу."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    fq, fa = fnt(img, 0.058), fnt(img, 0.044)
    img = veil(img, 0.06, 0.20, 130, s["light"])
    d = ImageDraw.Draw(img)
    y = int(H * 0.09)
    for ln in ST.wrap(d, data["question"], fq, int(W * 0.84)):
        put(d, (int(W * 0.08), y), ln, fq, s["fg"])
        y += int(fq.size * 1.16)
    lines = ST.wrap(d, data["answer"], fa, int(W * 0.78))
    h = int(len(lines) * fa.size * 1.3 + fa.size * 0.9)
    top = H - h - int(H * 0.13)
    img.alpha_composite(Image.new("RGBA", (int(W * 0.88), h), ACCENT + (240,)),
                        (int(W * 0.06), top))
    d = ImageDraw.Draw(img)
    yy = top + int(fa.size * 0.45)
    for ln in lines:
        put(d, (W // 2, yy), ln, fa, INK, anchor="ma")
        yy += int(fa.size * 1.3)
    return img


LAYOUTS = {
    "line": (line, "Одна фраза на плашці"),
    "title_sub": (title_sub, "Заголовок і пояснення під ним"),
    "steps": (steps, "Кроки з номерами в кружечках"),
    "bullets": (bullets, "Список із маркерами"),
    "versus": (versus, "Дві колонки з роздільником"),
    "stat": (stat, "Велика цифра як герой"),
    "quote": (quote, "Виділена думка з лапкою"),
    "card": (card, "Картка знизу: заголовок і абзац"),
    "bands": (bands, "Дві стрічки: тема зверху, висновок знизу"),
    "callout": (callout, "Виноска зі стрілкою до предмета"),
    "underline": (underline, "Заголовок з акцентним підкресленням"),
    "scale": (scale, "Шкала зі значенням"),
}

DATA = {
    "kicker": "Як заварювати",
    "headline": "ЧАГА ЛЮБИТЬ ТЕПЛО, А НЕ ОКРІП",
    "body": "Окріп руйнує частину сполук, заради яких чагу й заварюють. "
            "Дай воді постояти хвилину після закипання.",
    "steps": ["Залий гарячою, не окропом", "Настоюй 15 хвилин", "Проціди і пий теплим"],
    "points": ["Росте тільки на живій березі", "Зовні кірка, всередині руде",
               "Заварюється повторно", "Кофеїну не містить"],
    "columns": [
        {"title": "ЦІЛА", "points": ["Зберігається довше", "Заварюють кілька разів",
                                     "Треба час на відвар"]},
        {"title": "МЕЛЕНА", "points": ["Готова одразу", "Віддає все за раз",
                                       "Швидше вбирає вологу"]},
    ],
    "stat": "15",
    "stat_note": "хвилин настоювання — і настій готовий",
    "quote": "Чорна кірка зовні, руда серцевина всередині. Саме її й заварюють.",
    "callout": "Ця руда серцевина — те, заради чого чагу збирають",
    "question": "ОКРІП ЧИ ГАРЯЧА ВОДА?",
    "answer": "Гаряча. Окріп зайвий",
    "range": (0.55, 0.80),
    "value": "60–80 °C",
    "scale_lo": "холодна",
    "scale_hi": "окріп",
}


def main() -> int:
    if "--list" in sys.argv:
        for k, (_, about) in LAYOUTS.items():
            print(f"  {k:12} {about}")
        return 0

    OUTDIR.mkdir(parents=True, exist_ok=True)
    bases = {"dark": OUT_DIR / "looks" / "studio-dark.png",
             "light": OUT_DIR / "looks" / "knolling.png"}

    for name, path in bases.items():
        shots = []
        for key, (fn, _) in LAYOUTS.items():
            img = Image.open(path).convert("RGBA")
            out = fn(img, scheme(img), DATA).convert("RGB")
            out.save(OUTDIR / f"{name}_{key}.jpg", "JPEG", quality=91)
            shots.append(out)
            print(f"  ✔ {name}/{key}")
        tw = 236
        th = [i.resize((tw, int(tw * i.height / i.width))) for i in shots]
        cols = 6
        rows = (len(th) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (tw + 8), rows * (th[0].height + 8)),
                          (18, 18, 18))
        for i, t in enumerate(th):
            sheet.paste(t, ((i % cols) * (tw + 8), (i // cols) * (t.height + 8)))
        sheet.save(OUTDIR / f"_sheet_{name}.jpg", "JPEG", quality=87)
        print(f"  лист → _sheet_{name}.jpg\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
