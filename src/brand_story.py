# -*- coding: utf-8 -*-
"""Сторис в визуальном языке САМОГО бренда, на реальных фото товара.

Причина, по которой файл появился. Месяц мы рисовали абстрактные грибы
в тумане и клали на них свою типографику. Владелец раз за разом говорил
«что-то не то», и не мог сформулировать что. А потом я скачал его же
карточки товара из каталога — и там уже готовая система:

    заголовок пользой          «ФОКУС З РАНКУ»
    подзаголовок конкретикой   «120 КАПС | 30 ДНІВ КУРСУ | ВЕГАН»
    настоящая банка с логотипом
    инфографика в три колонки  «ГЕРИЦЕНОНИ → нейроген»
    таймлайн                   «1-2 тижні → 3-4 тижні → 30 днів»
    единый фон, утренний луг

То есть наши сторис были не похожи на его бренд. Они выглядели как
другой магазин. Никакая правка заголовков этого не лечит.

Палитра снята пипеткой с его же карточек, а не придумана.

    python brand_story.py
"""
import sys

from PIL import Image, ImageDraw, ImageFilter

import story_text as ST
from config import OUT_DIR

W, H = 1080, 1920
OUTDIR = OUT_DIR / "brand"

# Цвета сняты с out/real/*.jpg, а не выбраны на вкус
CREAM = (240, 235, 224)
FOREST = (26, 42, 19)
MUTED = (96, 104, 88)
LINE = (26, 42, 19, 40)


def fnt(k, bold=True):
    return ST.ImageFont.truetype(ST.FONT_BOLD if bold else ST.FONT_REG,
                                 max(14, int(W * k)))


def tracked(d, xy, text, f, fill, spacing=0.0, anchor_mid=False):
    """Текст с межбуквенным расстоянием — у него заголовки разрежены."""
    step = f.size * spacing
    total = sum(d.textlength(c, font=f) + step for c in text) - step
    x, y = xy
    if anchor_mid:
        x -= total / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + step
    return total


def stretch(photo):
    """Квадратное фото товара → вертикальный кадр 9:16.

    Первая версия достраивала верх и низ растянутой крайней СТРОКОЙ
    пикселей. На однородной кромке это незаметно, а на траве и окне даёт
    «расчёску» из вертикальных полос во весь экран — видно сразу.

    Поэтому поля заполняются тем же кадром, увеличенным до заполнения и
    сильно размытым. Приём стандартный для вертикального видео, и глаз
    читает его как продолжение сцены, а не как заплатку.
    """
    im = photo.convert("RGB")
    side = min(im.size)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2,
                  (im.width + side) // 2, (im.height + side) // 2))
    im = im.resize((W, W), Image.LANCZOS)

    k = max(W / im.width, H / im.height) * 1.25
    bg = im.resize((int(W * k), int(W * k)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                  (bg.width + W) // 2, (bg.height + H) // 2))
    bg = bg.filter(ImageFilter.GaussianBlur(46))

    canvas = Image.new("RGB", (W, H))
    canvas.paste(bg, (0, 0))
    canvas.paste(im, (0, int(H * 0.34)))
    return canvas


def haze(img, bottom, dark):
    """Мягкая подложка под текстовым блоком.

    Без неё подпись на траве не читается ни белым, ни тёмным: фон пёстрый.
    Цвет берётся по фону, чтобы на белой студийной карточке подложки
    вообще не было видно.
    """
    h = int(H * bottom)
    rgb = (12, 14, 10) if dark else (247, 244, 237)
    layer = Image.new("RGBA", (W, h))
    d = ImageDraw.Draw(layer)
    soft = int(h * 0.55)
    for y in range(h):
        k = 1.0 if y < h - soft else 1.0 - (y - (h - soft)) / soft
        d.line([(0, y), (W, y)], fill=rgb + (int(150 * k),))
    base = img.convert("RGBA")
    base.alpha_composite(layer, (0, 0))
    return base.convert("RGB")


def head_block(d, title, sub, y=None, ink=FOREST, sub_ink=MUTED):
    f = fnt(0.062)
    lines = ST.wrap(d, title.upper(), f, int(W * 0.86))
    y = y if y is not None else int(H * 0.085)
    for ln in lines:
        tracked(d, (W // 2, y), ln, f, ink, 0.02, anchor_mid=True)
        y += int(f.size * 1.18)
    if sub:
        fs = fnt(0.030, False)
        y += int(H * 0.008)
        tracked(d, (W // 2, y), sub.upper(), fs, sub_ink, 0.05, anchor_mid=True)
        y += int(fs.size * 1.6)
    return y


def columns(img, items, dark=False):
    """Три колонки «вещество → что за ним» — его приём с карточки."""
    d = ImageDraw.Draw(img)
    ink = CREAM if dark else FOREST
    sub_ink = (214, 210, 198) if dark else MUTED
    fk, fv = fnt(0.026), fnt(0.024, False)
    y = int(H * 0.30)
    step = W // (len(items) + 1)
    for i, (name, what) in enumerate(items, 1):
        x = step * i
        tracked(d, (x, y), name.upper(), fk, ink, 0.04, anchor_mid=True)
        w = d.textlength(what, font=fv)
        d.text((x - w / 2, y + int(fk.size * 1.7)), what, font=fv, fill=sub_ink)
    d.line([(int(W * 0.10), y - int(H * 0.022)),
            (int(W * 0.90), y - int(H * 0.022))], fill=LINE[:3], width=2)
    return img


def footer(img, text, dark_bg=False):
    """Строка действия внизу. Кремовой плашки нет намеренно: у него на
    карточках её тоже нет, а чужая полоса сразу выдаёт вставку."""
    d = ImageDraw.Draw(img)
    f = fnt(0.032)
    y = int(H * 0.905)
    ink = CREAM if dark_bg else FOREST
    d.line([(int(W * 0.34), y - int(H * 0.020)),
            (int(W * 0.66), y - int(H * 0.020))], fill=ink, width=2)
    tracked(d, (W // 2, y), text.upper(), f, ink, 0.04, anchor_mid=True)
    return img


def is_dark(img, top, bottom):
    """Тёмная ли зона под текстом — от этого цвет надписи."""
    band = img.crop((0, int(H * top), W, int(H * bottom))).convert("L")
    band = band.resize((32, 8))
    return sum(band.get_flattened_data()) / 256 < 128


def build(photo_path, title, sub, action, cols=None):
    img = stretch(Image.open(photo_path))
    dark_top = is_dark(img, 0.07, 0.26)
    img = haze(img, 0.30, dark_top)
    d = ImageDraw.Draw(img)
    head_block(d, title, sub, ink=CREAM if dark_top else FOREST,
               sub_ink=(214, 210, 198) if dark_top else MUTED)
    if cols:
        columns(img, cols, dark=dark_top)
    return footer(img, action, is_dark(img, 0.86, 0.95))


SHOTS = [
    # Только чистые фото: на m0-m3 у него уже стоит свой заголовок, и
    # наш ложится вторым — на кадре выходит два заголовка сразу.
    ("m4.jpg", "Чому мелений, а не капсули",
     "50 г · 25 днів курсу · веган", "Мелений — на сайті", None),
    ("m9.jpg", "Що всередині", "їжовик гребінчастий · мелені плодові тіла",
     "Склад — на картці", [("Гериценони", "мʼякоть гриба"),
                           ("Глюкани", "цукрові ланцюги"),
                           ("Поліфеноли", "темні барвники")]),
    ("m6.jpg", "Заварив — і викинув гущу?", "смолисте лишається в осаді",
     "Пий разом з осадом", None),
]


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    shots = []
    for name, title, sub, action, cols in SHOTS:
        out = build(OUT_DIR / "real" / "all" / name, title, sub, action, cols)
        dest = OUTDIR / name.replace(".jpg", "_story.jpg")
        out.save(dest, "JPEG", quality=92)
        shots.append(out)
        print(f"  ✔ {dest.name}")
    tw = 420
    th = [i.resize((tw, int(tw * i.height / i.width))) for i in shots]
    page = Image.new("RGB", (len(th) * (tw + 12) + 12, th[0].height + 24),
                     (30, 30, 30))
    for i, im in enumerate(th):
        page.paste(im, (12 + i * (tw + 12), 12))
    page.save(OUTDIR / "_sheet.jpg", "JPEG", quality=92)
    print(f"лист: {OUTDIR / '_sheet.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
