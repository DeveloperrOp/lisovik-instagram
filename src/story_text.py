# -*- coding: utf-8 -*-
"""Надпись поверх кадра — так, как её печатают в самих сторис.

Не вёрстка плаката. В настоящих сторис текст выглядит как то, что человек
набрал пальцем поверх своего фото: простой гротеск, белым, иногда на
плашке, прижат к одному краю и не разложен по сетке.

Три вида, все взяты из того, что реально есть в редакторе Instagram:
    plain      — белым с мягкой тенью
    box        — белым на тёмной полупрозрачной плашке со скруглением
    highlight  — каждая строка на своей заливке, плашка обнимает текст

    python story_text.py out/shots/ritual-chaga.png box "ЧАГА ЛЮБИТЬ ТЕПЛО"

Текст рисует PIL, а не модель: у модели на длинной фразе орфография
ломается, а вычитать её нечем — читающая модель молча исправляет опечатки.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"

WHITE = (255, 255, 255)
INK = (22, 22, 24)


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        probe = f"{cur} {w}".strip()
        if d.textlength(probe, font=fnt) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(d, text, path, size, max_w, floor=30):
    while size > floor:
        fnt = ImageFont.truetype(path, size)
        if all(d.textlength(l, font=fnt) <= max_w
               for l in wrap(d, text, fnt, max_w)):
            return fnt
        size -= 2
    return ImageFont.truetype(path, floor)


def soft_shadow(img, lines, fnt, box, gap, align_x):
    """Тень отдельным слоем с размытием — иначе белое по светлому пропадает."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    y = box[1]
    for line in lines:
        ld.text((align_x, y), line, font=fnt, fill=(0, 0, 0, 170), anchor="ma")
        y += gap
    layer = layer.filter(ImageFilter.GaussianBlur(9))
    return Image.alpha_composite(img, layer)


def draw(img: Image.Image, text: str, kind="box", pos=0.30,
         accent=(255, 209, 45), scale=0.058) -> Image.Image:
    """Кладёт надпись на кадр. pos — доля высоты, где начинается блок.

    Кегль задаётся долей ШИРИНЫ кадра, а не пикселями: подложки приходят
    в 1536 или 1080 точек, и один и тот же абсолютный размер выглядит на
    них по-разному — на большом холсте текст выглядит мелким.
    """
    img = img.convert("RGBA")
    W, H = img.size
    d = ImageDraw.Draw(img)
    max_w = int(W * 0.80)

    fnt = fit(d, text, FONT_BOLD, int(W * scale), max_w,
              floor=int(W * 0.030))
    lines = wrap(d, text, fnt, max_w)
    gap = int(fnt.size * 1.34)
    cx = W // 2
    top = int(H * pos)

    if kind == "plain":
        img = soft_shadow(img, lines, fnt, (0, top), gap, cx)
        d = ImageDraw.Draw(img)
        y = top
        for line in lines:
            d.text((cx, y), line, font=fnt, fill=WHITE, anchor="ma")
            y += gap
        return img

    if kind == "highlight":
        # Плашка обнимает каждую строку по её ширине — классический вид
        # «выделенного» текста в редакторе Instagram
        pad_x, pad_y = int(fnt.size * 0.34), int(fnt.size * 0.16)
        y = top
        for line in lines:
            w = d.textlength(line, font=fnt)
            box = (cx - w / 2 - pad_x, y - pad_y,
                   cx + w / 2 + pad_x, y + fnt.size + pad_y)
            d.rounded_rectangle(box, radius=int(fnt.size * 0.22), fill=accent)
            d.text((cx, y), line, font=fnt, fill=INK, anchor="ma")
            y += gap
        return img

    # box — одна общая плашка под всеми строками
    widest = max(d.textlength(l, font=fnt) for l in lines)
    pad_x, pad_y = int(fnt.size * 0.52), int(fnt.size * 0.42)
    h = gap * (len(lines) - 1) + fnt.size
    box = (cx - widest / 2 - pad_x, top - pad_y,
           cx + widest / 2 + pad_x, top + h + pad_y)

    panel = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle(
        box, radius=int(fnt.size * 0.34), fill=(18, 18, 20, 205))
    img = Image.alpha_composite(img, panel)

    d = ImageDraw.Draw(img)
    y = top
    for line in lines:
        d.text((cx, y), line, font=fnt, fill=WHITE, anchor="ma")
        y += gap
    return img


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    src, kind, text = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    out = draw(Image.open(src), text, kind).convert("RGB")
    dest = src.with_name(f"{src.stem}_{kind}.jpg")
    out.save(dest, "JPEG", quality=92)
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
