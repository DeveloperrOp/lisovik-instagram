# -*- coding: utf-8 -*-
"""Розкладки для стрічки. Це НЕ сторіс.

Ярик 10.09, подивившись першу спробу: «не годится, я же просил посмотреть
как выглядят по дизайну прошлые посты и вообще не хочу чтобы посты были
как сторис».

Знято з наших же опублікованих каруселей (Жіноча формула 13.08, MEN
11.08, Тремела 08.08). Мова стрічки інша, ніж у сторіс:

    сторіс                          стрічка
    ─────────────────────────────   ──────────────────────────────
    жовта плашка з кікером          нічого жовтого взагалі
    заголовок на пів екрана         заголовок угорі, спокійніший
    банка збоку, як реквізит        банка — герой, стоїть у природі
    жовта смуга з дією внизу        внизу факти з лінійними іконками
    студія або кухня                золота година, тепле боке
    текст білий на затемненні       темно-зелений угорі на світлому,
                                    кремовий унизу на затемненні

Кольори взяті піпеткою з тих постів, не вигадані.
"""
from PIL import Image, ImageDraw, ImageFilter

import story_text as ST

W, H = 1080, 1350

FOREST = (45, 61, 36)          # темно-зелений заголовок на світлому небі
CREAM = (245, 238, 224)        # кремовий текст на затемненні
CREAM_DIM = (222, 214, 198)


def font(px: int, bold=True):
    return ST.ImageFont.truetype(ST.FONT_BOLD if bold else ST.FONT_REG, px)


def veil_top(img: Image.Image, h: int, power=150) -> Image.Image:
    """Легке освітлення верху: заголовок мусить читатись на будь-якому небі."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for y in range(h):
        a = int(power * (1 - y / h) ** 1.4)
        d.line([(0, y), (img.width, y)], fill=(252, 248, 240, a))
    return Image.alpha_composite(img, lay)


def veil_bottom(img: Image.Image, h: int, power=250) -> Image.Image:
    """Затемнення під факти.

    У наших постах низ — суцільна майже чорна плашка без деталей, а не
    легка тінь: тільки так кремовий текст читається поверх освітленої
    сонцем трави. Тому верхня третина смуги — плавний вхід, а нижні дві
    третини вже суцільні. Одного градієнта на всю висоту не вистачало:
    саме там, де стоять іконки, трава ще просвічувала.
    """
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    top = img.height - h
    ramp = int(h * 0.34)
    for y in range(h):
        a = power if y >= ramp else int(power * (y / ramp) ** 0.85)
        d.line([(0, top + y), (img.width, top + y)], fill=(12, 16, 10, a))
    return Image.alpha_composite(img, lay)


# ----------------------------------------------------------- іконки
# Лінійні, в одну товщину, як у зразках. Малюємо кодом: готових файлів
# немає, а модель на такому дрібному масштабі малює кашу.

def _ring(d, box, col, w):
    d.ellipse(box, outline=col, width=w)


def ic_drop(d, x, y, s, col, w):
    """Крапля — риб'ячий жир."""
    d.polygon([(x, y - s), (x + s * 0.72, y + s * 0.28),
               (x - s * 0.72, y + s * 0.28)], outline=col, width=w)
    d.arc([x - s * 0.72, y - s * 0.44, x + s * 0.72, y + s * 1.0],
          start=0, end=180, fill=col, width=w)


def ic_atom(d, x, y, s, col, w, label="Mg"):
    """Атом із підписом — мінерал."""
    _ring(d, [x - s, y - s * 0.42, x + s, y + s * 0.42], col, w)
    _ring(d, [x - s * 0.42, y - s, x + s * 0.42, y + s], col, w)
    f = font(int(s * 0.78))
    d.text((x, y), label, font=f, fill=col, anchor="mm")


def ic_clock(d, x, y, s, col, w):
    """Годинник — коли приймати."""
    _ring(d, [x - s, y - s, x + s, y + s], col, w)
    d.line([(x, y), (x, y - s * 0.55)], fill=col, width=w)
    d.line([(x, y), (x + s * 0.45, y)], fill=col, width=w)


def ic_calendar(d, x, y, s, col, w):
    """Календар — щодня, без пропусків."""
    d.rounded_rectangle([x - s, y - s * 0.82, x + s, y + s * 0.88],
                        radius=int(s * 0.18), outline=col, width=w)
    d.line([(x - s, y - s * 0.34), (x + s, y - s * 0.34)], fill=col, width=w)
    for dx in (-0.5, 0.0, 0.5):
        d.line([(x + s * dx - s * 0.16, y + s * 0.22),
                (x + s * dx - s * 0.02, y + s * 0.40)], fill=col, width=w)
        d.line([(x + s * dx - s * 0.02, y + s * 0.40),
                (x + s * dx + s * 0.22, y + s * 0.02)], fill=col, width=w)


def ic_capsule(d, x, y, s, col, w):
    """Капсула — скільки в курсі."""
    d.rounded_rectangle([x - s, y - s * 0.42, x + s, y + s * 0.42],
                        radius=int(s * 0.42), outline=col, width=w)
    d.line([(x, y - s * 0.42), (x, y + s * 0.42)], fill=col, width=w)


def ic_leaf(d, x, y, s, col, w):
    """Лист — рослинна частина складу."""
    d.arc([x - s, y - s, x + s, y + s], start=200, end=20, fill=col, width=w)
    d.arc([x - s, y - s, x + s, y + s], start=20, end=200, fill=col, width=w)
    d.line([(x - s * 0.7, y + s * 0.7), (x + s * 0.7, y - s * 0.7)],
           fill=col, width=w)


ICONS = {"drop": ic_drop, "atom": ic_atom, "clock": ic_clock,
         "calendar": ic_calendar, "capsule": ic_capsule, "leaf": ic_leaf}


def title(img, text, top_ratio=0.055, scale=0.088, col=FOREST, max_w=0.86):
    """Заголовок угорі по центру. У зразках він темно-зелений і спокійний:
    не кричить на пів кадру, як у сторіс, а називає розділ."""
    d = ImageDraw.Draw(img)
    f = font(int(W * scale))
    lines = ST.wrap(d, text.upper(), f, int(W * max_w))
    while len(lines) > 2 and f.size > int(W * 0.055):
        f = font(int(f.size * 0.94))
        lines = ST.wrap(d, text.upper(), f, int(W * max_w))
    y = int(H * top_ratio)
    for ln in lines:
        d.text((W // 2, y), ln, font=f, fill=col, anchor="ma")
        y += int(f.size * 1.08)
    return y


def subtitle(img, text, y, col=FOREST, scale=0.038):
    d = ImageDraw.Draw(img)
    f = font(int(W * scale), bold=False)
    y += int(H * 0.012)
    for ln in ST.wrap(d, text, f, int(W * 0.78)):
        d.text((W // 2, y), ln, font=f, fill=col, anchor="ma")
        y += int(f.size * 1.30)
    return y


def facts_row(img, facts, band=0.26):
    """Смуга фактів унизу: іконка, жирний рядок, підпис.

    Саме цим пости й відрізняються від сторіс — замість жовтої плашки з
    дією тут стоїть склад або схема, і читається він як картка товару.

    Уся група живе ВСЕРЕДИНІ затемненої смуги: у першій спробі іконки
    стояли вище неї, на рівні етикеток, і налазили на банки.
    """
    img = veil_bottom(img, int(H * band))
    d = ImageDraw.Draw(img)
    n = len(facts)
    cell = W / n
    fb = font(int(W * 0.031))
    fs = font(int(W * 0.026), bold=False)
    y_icon = H - int(H * band * 0.60)
    y_head = H - int(H * band * 0.38)
    for i, f in enumerate(facts):
        cx = int(cell * (i + 0.5))
        draw_icon = ICONS.get(f.get("icon", "leaf"), ic_leaf)
        args = dict(col=CREAM, w=max(2, int(W * 0.0042)))
        if draw_icon is ic_atom:
            args["label"] = f.get("mark", "Mg")
        draw_icon(d, cx, y_icon, int(W * 0.042), **args)
        y = y_head
        for ln in ST.wrap(d, f["head"].upper(), fb, int(cell * 0.92)):
            d.text((cx, y), ln, font=fb, fill=CREAM, anchor="ma")
            y += int(fb.size * 1.14)
        for ln in ST.wrap(d, f.get("sub", ""), fs, int(cell * 0.90)):
            d.text((cx, y), ln, font=fs, fill=CREAM_DIM, anchor="ma")
            y += int(fs.size * 1.20)
    return img


def steps_col(img, steps, start=0.30):
    """Кроки стовпчиком: іконка ліворуч, жирний рядок, під ним пояснення.
    Так у нас зроблено «ЯК ПРИЙМАТИ» у пості про жіночу формулу."""
    d = ImageDraw.Draw(img)
    fb = font(int(W * 0.058))
    fs = font(int(W * 0.040), bold=False)
    x_ic, x_tx = int(W * 0.155), int(W * 0.275)
    y = int(H * start)
    for s in steps:
        draw_icon = ICONS.get(s.get("icon", "leaf"), ic_leaf)
        args = dict(col=FOREST, w=max(2, int(W * 0.005)))
        if draw_icon is ic_atom:
            args["label"] = s.get("mark", "Mg")
        draw_icon(d, x_ic, y + int(fb.size * 0.62), int(W * 0.048), **args)
        d.text((x_tx, y), s["head"].upper(), font=fb, fill=FOREST)
        y += int(fb.size * 1.06)
        for ln in ST.wrap(d, s.get("sub", ""), fs, int(W * 0.62)):
            d.text((x_tx, y), ln, font=fs, fill=FOREST)
            y += int(fs.size * 1.24)
        y += int(H * 0.042)
    return img
