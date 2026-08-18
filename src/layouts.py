# -*- coding: utf-8 -*-
"""Вёрстка сторис по типам.

Каждый тип выглядит по-своему — иначе лента читается как одно фото,
повторённое 28 раз. Модели доверяем только сцену и крупный заголовок
товарного кадра; всю структуру (шаги, колонки, цитаты) рисует PIL,
потому что структуру модель не держит.

Типы:
    product  — реальный товар крупно, польза + характеристики
    fact     — один факт, крупная типографика поверх приглушённой сцены
    howto    — три пронумерованных шага
    compare  — два варианта в колонках
    review   — цитата клиента
    ask      — фон под стикер вопросов
    mood     — сцена почти без текста
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"

CREAM = (247, 244, 236)
DIM = (214, 210, 199)
MOSS = (143, 168, 106)
INK = (18, 24, 18)


def font(path, size):
    return ImageFont.truetype(path, size)


def fit_to_story(img: Image.Image) -> Image.Image:
    """Центральный кроп до 9:16 и ресайз в 1080x1920."""
    target = W / H
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / target)
        top = (h - nh) // 2
        img = img.crop((0, top, w, top + nh))
    return img.resize((W, H), Image.LANCZOS).convert("RGBA")


def veil(img: Image.Image, strength=150) -> Image.Image:
    """Равномерная затемняющая вуаль — чтобы текст читался поверх сцены."""
    layer = Image.new("RGBA", (W, H), (10, 16, 12, strength))
    return Image.alpha_composite(img, layer)


def gradient(img: Image.Image, height=620, strength=225, top=False) -> Image.Image:
    """Градиент снизу (или сверху) под мелкий текст."""
    mask = Image.new("L", (1, height))
    for y in range(height):
        v = y / height
        mask.putpixel((0, y), int(strength * (v ** 1.6)))
    mask = mask.resize((W, height))
    if top:
        mask = mask.transpose(Image.FLIP_TOP_BOTTOM)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", (W, height), (8, 14, 10, 255)),
                (0, 0 if top else H - height), mask)
    return Image.alpha_composite(img, layer)


def wrap(draw, text, fnt, max_w):
    """Перенос по словам под заданную ширину."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        probe = f"{cur} {word}".strip()
        if draw.textlength(probe, font=fnt) <= max_w or not cur:
            cur = probe
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, path, size, max_w, min_size=34):
    """Подбирает размер шрифта, пока текст не влезет по ширине.

    Перенос по словам не спасает от длинного слова: «ЯСКРАВО-ПОМАРАНЧЕВИЙ»
    в одну строку не помещается и обрезается по краю кадра.
    """
    while size > min_size:
        fnt = font(path, size)
        if all(draw.textlength(ln, font=fnt) <= max_w
               for ln in wrap(draw, text, fnt, max_w)):
            return fnt
        size -= 4
    return font(path, min_size)


def shadowed(d, xy, text, fnt, fill=CREAM, anchor="mm", blur=True):
    if blur:
        d.text((xy[0] + 2, xy[1] + 3), text, font=fnt, fill=(0, 0, 0, 150), anchor=anchor)
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def block(d, lines, fnt, y, gap, fill=CREAM, anchor="mm", x=W // 2):
    """Рисует список строк сверху вниз, возвращает нижнюю границу."""
    for line in lines:
        shadowed(d, (x, y), line, fnt, fill=fill, anchor=anchor)
        y += gap
    return y


def footer(img, cta, disclaimer):
    """Общий низ: призыв и дисклеймер. Есть на каждом кадре."""
    d = ImageDraw.Draw(img)
    f_cta = font(FONT_BOLD, 42)
    f_disc = font(FONT_REG, 24)
    shadowed(d, (W // 2, H - 168), cta, f_cta)
    parts = disclaimer.split(". ")
    l1 = ". ".join(parts[:2]) + ("." if len(parts) > 2 else "")
    l2 = ". ".join(parts[2:])
    shadowed(d, (W // 2, H - 108), l1, f_disc, fill=DIM, blur=False)
    if l2:
        shadowed(d, (W // 2, H - 76), l2, f_disc, fill=DIM, blur=False)
    return img


# ---------------------------------------------------------------- типы

def product(bg, item):
    """Товар крупно, заголовок — польза, подпись — фасовка.

    Текст рисует PIL, а не модель: получив свободу, она подкладывает под
    заголовок светлую плашку и меняет гарнитуру от кадра к кадру.
    """
    img = fit_to_story(bg)
    img = gradient(img, height=560, strength=175, top=True)
    img = gradient(img)
    d = ImageDraw.Draw(img)

    f_h = fit(d, item["headline"], FONT_BOLD, 86, W - 140)
    lines = wrap(d, item["headline"], f_h, W - 140)
    y = block(d, lines, f_h, 250, int(f_h.size * 1.12))

    if item.get("subline"):
        f_s = fit(d, item["subline"], FONT_SEMI, 48, W - 200)
        shadowed(d, (W // 2, y + 18), item["subline"], f_s, fill=CREAM)
    return img


def fact(bg, item):
    """Один факт. Крупная типографика по центру, сцена приглушена."""
    img = veil(fit_to_story(bg), 165)
    d = ImageDraw.Draw(img)
    f_h = fit(d, item["headline"], FONT_BOLD, 92, W - 150)
    f_s = font(FONT_REG, 44)

    lines = wrap(d, item["headline"], f_h, W - 150)
    gap = int(f_h.size * 1.1)
    y = H // 2 - (len(lines) * gap) // 2 - 60
    y = block(d, lines, f_h, y, gap)

    d.line([(W // 2 - 60, y + 6), (W // 2 + 60, y + 6)], fill=MOSS, width=4)

    if item.get("subline"):
        sub = wrap(d, item["subline"], f_s, W - 220)
        block(d, sub, f_s, y + 68, 56, fill=DIM)
    return img


def useful(bg, item):
    """Корисне: заголовок, пояснення на 2-4 рядки і практичний висновок.

    Замінює колишній «факт»: сам по собі факт про гриби — це ерудиція,
    а не користь. Тут кадр відповідає на питання «і що мені з цього».
    """
    img = veil(fit_to_story(bg), 185)
    d = ImageDraw.Draw(img)

    f_h = fit(d, item["headline"], FONT_BOLD, 78, W - 130)
    f_b = font(FONT_REG, 50)
    f_t = font(FONT_SEMI, 46)

    lines = wrap(d, item["headline"], f_h, W - 130)
    y = block(d, lines, f_h, 250, int(f_h.size * 1.14))

    d.line([(W // 2 - 56, y + 16), (W // 2 + 56, y + 16)], fill=MOSS, width=4)
    y += 92

    body_lines = wrap(d, item.get("body", ""), f_b, W - 150)
    for ln in body_lines:
        shadowed(d, (W // 2, y), ln, f_b, fill=CREAM)
        y += 68

    # Вывод прижимаем к низу, а не клеим сразу под текстом: иначе половина
    # кадра пустует, а на неё влезает ещё пара строк пользы
    if item.get("tip"):
        tip_lines = wrap(d, item["tip"], f_t, W - 210)
        h = len(tip_lines) * 58 + 52
        top = H - 300 - h
        panel = Image.new("RGBA", (W - 140, h), (26, 44, 28, 180))
        img.alpha_composite(panel, (70, top))
        d = ImageDraw.Draw(img)
        ty = top + 26 + 29
        for ln in tip_lines:
            shadowed(d, (W // 2, ty), ln, f_t, fill=(208, 226, 178))
            ty += 58
    return img


def mistake(bg, item):
    """Помилка новачка: що роблять не так і як правильно.

    Найсильніший формат для залучення — люди впізнають себе.
    """
    img = veil(fit_to_story(bg), 190)
    d = ImageDraw.Draw(img)

    f_h = fit(d, item.get("headline", "ПОМИЛКА НОВАЧКА"), FONT_BOLD, 72, W - 150)
    f_l = font(FONT_BOLD, 40)
    f_b = font(FONT_REG, 46)

    lines = wrap(d, item.get("headline", "ПОМИЛКА НОВАЧКА"), f_h, W - 150)
    y = block(d, lines, f_h, 330, int(f_h.size * 1.14))
    y += 70

    x = 110
    for label, text, colour in (
        ("ЯК ЧАСТО РОБЛЯТЬ", item.get("wrong", ""), (214, 128, 110)),
        ("ЯК КРАЩЕ", item.get("right", ""), (150, 190, 120)),
    ):
        d.line([(x, y - 6), (x, y + 6 + 56 * len(wrap(d, text, f_b, W - 260)))],
               fill=colour, width=4)
        shadowed(d, (x + 30, y), label, f_l, fill=colour, anchor="lm", blur=False)
        y += 62
        for ln in wrap(d, text, f_b, W - 260):
            shadowed(d, (x + 30, y), ln, f_b, fill=CREAM, anchor="lm")
            y += 56
        y += 60

    if item.get("why"):
        for ln in wrap(d, item["why"], font(FONT_SEMI, 40), W - 200):
            shadowed(d, (W // 2, y), ln, font(FONT_SEMI, 40), fill=DIM)
            y += 50
    return img


def myth(bg, item):
    """Міф: що кажуть -> як насправді -> чому так вийшло.

    Відрізняється від «помилки»: там неправильна дія, тут неправильне
    уявлення. Візуально теж інакше — твердження закреслене.
    """
    img = veil(fit_to_story(bg), 190)
    d = ImageDraw.Draw(img)

    f_h = fit(d, item["headline"], FONT_BOLD, 74, W - 140)
    f_l = font(FONT_BOLD, 36)
    f_c = font(FONT_REG, 46)
    f_t = font(FONT_SEMI, 50)
    f_w = font(FONT_REG, 42)

    lines = wrap(d, item["headline"], f_h, W - 140)
    y = block(d, lines, f_h, 300, int(f_h.size * 1.14))
    y += 60

    # що кажуть — приглушено і закреслено
    shadowed(d, (W // 2, y), "КАЖУТЬ", f_l, fill=(198, 132, 116), blur=False)
    y += 62
    for ln in wrap(d, item.get("claim", ""), f_c, W - 190):
        shadowed(d, (W // 2, y), ln, f_c, fill=(186, 182, 172))
        w = d.textlength(ln, font=f_c)
        d.line([(W // 2 - w / 2, y + 2), (W // 2 + w / 2, y + 2)],
               fill=(198, 132, 116), width=3)
        y += 60

    y += 46
    shadowed(d, (W // 2, y), "НАСПРАВДІ", f_l, fill=MOSS, blur=False)
    y += 66
    for ln in wrap(d, item.get("truth", ""), f_t, W - 170):
        shadowed(d, (W // 2, y), ln, f_t, fill=CREAM)
        y += 64

    if item.get("why"):
        y += 40
        for ln in wrap(d, item["why"], f_w, W - 190):
            shadowed(d, (W // 2, y), ln, f_w, fill=DIM)
            y += 54
    return img


def howto(bg, item):
    """Три шага. Нумерация — потому что порядок здесь действительно важен."""
    img = veil(fit_to_story(bg), 175)
    d = ImageDraw.Draw(img)
    f_h = fit(d, item["headline"], FONT_BOLD, 78, W - 150)
    f_n = font(FONT_BOLD, 40)
    f_s = font(FONT_SEMI, 44)

    lines = wrap(d, item["headline"], f_h, W - 150)
    y = block(d, lines, f_h, 380, int(f_h.size * 1.15))
    y += 60

    for n, step in enumerate(item.get("steps", []), 1):
        cx = 150
        d.ellipse([cx - 34, y - 34, cx + 34, y + 34], outline=MOSS, width=4)
        shadowed(d, (cx, y - 2), str(n), f_n, fill=MOSS, blur=False)
        for i, ln in enumerate(wrap(d, step, f_s, W - 300)):
            shadowed(d, (cx + 66, y - 2 + i * 52), ln, f_s, anchor="lm")
        y += 148
    return img


def compare(bg, item):
    """Два варіанти поруч, у кожного список переваг.

    Одного рядка на колонку мало: «більше білка» проти «насиченіший смак» —
    це не порівняння, а вода. Людина має побачити по чотири-пʼять пунктів
    і сама вирішити, що їй ближче.
    """
    img = veil(fit_to_story(bg), 180)
    d = ImageDraw.Draw(img)
    f_h = fit(d, item["headline"], FONT_BOLD, 72, W - 140)
    f_o = font(FONT_BOLD, 54)
    f_p = font(FONT_REG, 40)

    lines = wrap(d, item["headline"], f_h, W - 140)
    y = block(d, lines, f_h, 300, int(f_h.size * 1.14))

    top = y + 60
    bottom = H - 330
    d.line([(W // 2, top), (W // 2, bottom)], fill=(255, 255, 255, 55), width=2)

    col_w = W // 2 - 90
    for idx, opt in enumerate(item.get("options", [])[:2]):
        cx = W // 4 + idx * (W // 2)
        shadowed(d, (cx, top + 50), opt.get("title", ""), f_o, fill=MOSS)
        yy = top + 146

        points = opt.get("points")
        if not points:
            points = [opt.get("text", "")]
        for pt in points:
            if not pt:
                continue
            plines = wrap(d, pt, f_p, col_w - 34)
            # маркер тільки біля першого рядка пункту
            d.ellipse([cx - col_w // 2 + 2, yy - 5, cx - col_w // 2 + 12, yy + 5],
                      fill=MOSS)
            for k, ln in enumerate(plines):
                shadowed(d, (cx - col_w // 2 + 28, yy), ln, f_p,
                         fill=CREAM, anchor="lm")
                yy += 50
            yy += 22
    return img


def review(bg, item):
    """Цитата клиента. Тексты вычитывает человек — медицинских обещаний быть не должно."""
    img = veil(fit_to_story(bg), 190)
    d = ImageDraw.Draw(img)
    f_t = font(FONT_SEMI, 66)
    f_a = font(FONT_REG, 40)

    # Вместо типографской кавычки — короткая черта: «...» в шрифте
    # читается как двойная стрелка и выглядит мусором
    d.line([(W // 2 - 46, 470), (W // 2 + 46, 470)], fill=MOSS, width=5)

    lines = wrap(d, item.get("quote", ""), f_t, W - 180)
    y = block(d, lines, f_t, 600, 84)
    if item.get("author"):
        shadowed(d, (W // 2, y + 46), item["author"], f_a, fill=DIM, blur=False)
    return img


def ask(bg, item):
    """Фон под стикер вопросов. Публикуется руками — API стикеры не умеет."""
    img = veil(fit_to_story(bg), 150)
    d = ImageDraw.Draw(img)
    f_h = fit(d, item["headline"], FONT_BOLD, 84, W - 160)
    lines = wrap(d, item["headline"], f_h, W - 160)
    y = block(d, lines, f_h, 420, int(f_h.size * 1.15))
    if item.get("subline"):
        shadowed(d, (W // 2, y + 30), item["subline"], font(FONT_REG, 44), fill=DIM)
    return img


def mood(bg, item):
    """Сцена почти без текста — передышка между продающими кадрами.

    Верхний градиент обязателен: сцены тут светлые (рассвет, лучи),
    и без подложки белый заголовок на них просто исчезает.
    """
    img = fit_to_story(bg)
    # Сцены здесь светлые — рассвет, лучи сквозь стволы. Слабая подложка
    # текст не спасает: солнце оказывается ровно за заголовком.
    img = gradient(img, height=700, strength=245, top=True)
    img = gradient(img, height=520, strength=190)
    d = ImageDraw.Draw(img)
    f_h = fit(d, item["headline"], FONT_BOLD, 76, W - 160)
    f_s = font(FONT_REG, 42)
    shadowed(d, (W // 2, 300), item["headline"], f_h)
    shadowed(d, (W // 2, 300), item["headline"], f_h, blur=False)   # плотнее
    if item.get("subline"):
        shadowed(d, (W // 2, 390), item["subline"], f_s, fill=DIM)
    return img


RENDERERS = {
    "product": product, "useful": useful, "mistake": mistake, "myth": myth,
    "howto": howto, "compare": compare, "review": review, "ask": ask,
    "fact": fact, "mood": mood,        # старые типы, оставлены для совместимости
}


def render(kind: str, bg: Image.Image, item: dict, cta: str, disclaimer: str):
    fn = RENDERERS.get(kind)
    if not fn:
        raise ValueError(f"неизвестный тип сторис: {kind}")
    img = fn(bg, item)
    return footer(img, cta, disclaimer).convert("RGB")
