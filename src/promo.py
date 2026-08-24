# -*- coding: utf-8 -*-
"""Разовая акция: пост в ленту + сторис по дням.

Отдельный модуль, а не новый тип в layouts.py, по двум причинам:
у поста другая геометрия (1080x1350 против 1080x1920), а вся вёрстка
сторис завязана на модульные W/H; и ежедневный публикатор сейчас работает
каждый день — лезть в него ради разовой акции незачем.

    python promo.py --gen        # нарисовать подложки через Vertex
    python promo.py --compose    # собрать кадры поверх подложек
    python promo.py              # и то, и другое

Готовое кладётся в out/promo/. Публикацией занимается publish.py уже
после того, как Ярик посмотрел и одобрил.
"""
import sys
import time

import yaml
from PIL import Image, ImageDraw

import generate as gen
import layouts as L
from config import CONTENT_DIR, OUT_DIR

PLAN = CONTENT_DIR / "promo_independence.yaml"
PENDING = OUT_DIR / "pending"
PROMO = OUT_DIR / "promo"

# Тёплый акцент вместо брендовой зелени: под День Независимости золото
# по синему сумраку читается как национальные цвета, но без флага в кадре
GOLD = (233, 186, 82)
WARM = (247, 232, 200)

# Жёлто-синее берём цветом дизайна, а не флагом в кадре. Синий взят глубже
# флажного: чистый #0057B7 на весь кадр даёт «дешёвый баннер», а тёмный
# держит премиальность и при этом жёлтый на нём горит.
UA_BLUE = (13, 54, 133)
UA_BLUE_DEEP = (6, 25, 66)
UA_YELLOW = (255, 209, 45)
INK_BLUE = (8, 30, 74)


def duotone(img, dark, light):
    """Перекраска фото в два цвета по яркости.

    Тени уходят в синий, света — в жёлтый. Лес остаётся узнаваемым,
    но кадр читается как дизайн, а не как фотосток.
    """
    g = img.convert("L")
    lut = []
    for c in range(3):
        lut += [int(dark[c] + (light[c] - dark[c]) * i / 255) for i in range(256)]
    return g.convert("RGB").point(lut).convert("RGBA")


def flat(w, h, top_c, bottom_c):
    """Вертикальная заливка — фон без фотографии."""
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        img.putpixel((0, y), tuple(int(top_c[c] + (bottom_c[c] - top_c[c]) * t)
                                   for c in range(3)))
    return img.resize((w, h)).convert("RGBA")


# ------------------------------------------------------- холст любого размера
# layouts.* завязаны на модульные W/H сторис, поэтому операции с холстом
# здесь свои, а размер приходит параметром.

def fit_canvas(img: Image.Image, w: int, h: int) -> Image.Image:
    """Центральный кроп под нужное соотношение и ресайз."""
    target = w / h
    iw, ih = img.size
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        top = (ih - nh) // 2
        img = img.crop((0, top, iw, top + nh))
    return img.resize((w, h), Image.LANCZOS).convert("RGBA")


def veil(img, w, h, strength):
    return Image.alpha_composite(img, Image.new("RGBA", (w, h), (8, 14, 22, strength)))


def gradient(img, w, h, height, strength, top=False):
    """Затемнение снизу или сверху — под мелкий текст."""
    mask = Image.new("L", (1, height))
    for y in range(height):
        v = y / height
        mask.putpixel((0, y), int((1 - v if top else v) * strength))
    mask = mask.resize((w, height))
    layer = Image.new("RGBA", (w, height), (8, 14, 22, 255))
    layer.putalpha(mask)
    img.alpha_composite(layer, (0, 0 if top else h - height))
    return img


def rule(d, cx, y, half=70, color=GOLD, width=5):
    d.line([(cx - half, y), (cx + half, y)], fill=color, width=width)


def fit_one_line(d, text, path, size, max_w, floor):
    """Кегль под заголовок, который обязан остаться в одну строку.

    layouts.fit следит лишь за тем, чтобы влезла каждая строка ПОСЛЕ переноса,
    поэтому «-20% НА ВСЕ» он спокойно ломает на «-20% НА» и «ВСЕ». Для акции
    такой перенос — брак: цифра скидки должна читаться одним куском.
    Если в одну строку не выходит даже на floor, отдаём обычный перенос.
    """
    while size > floor:
        fnt = L.font(path, size)
        if d.textlength(text, font=fnt) <= max_w:
            return fnt, [text]
        size -= 4
    fnt = L.fit(d, text, path, size, max_w, min_size=floor - 20)
    return fnt, L.wrap(d, text, fnt, max_w)


# ------------------------------------------------------------------- вёрстка

def render(item: dict, bg: Image.Image, cfg: dict, w: int, h: int) -> Image.Image:
    """Общая вёрстка акции: кикер, крупный заголовок, даты, сноска, футер.

    Одна раскладка на пост и на сторис — меняются только размеры и отступы,
    иначе четыре кадра акции разъедутся по стилю.
    """
    story = h > w * 1.5           # сторис вытянутее, чем пост 4:5

    design = item.get("design", cfg.get("design", "duotone"))

    if design == "solid":
        # Фотографии нет вовсе: плотный синий и жёлтая типографика.
        # Самый заметный вариант в ленте, но бренд теряет лес.
        img = flat(w, h, UA_BLUE, UA_BLUE_DEEP)
        head_c, kick_c = UA_YELLOW, UA_YELLOW
        sub_c, note_c = WARM, (176, 196, 232)
    elif design in ("band", "band-duo"):
        # Фото приглушаем, заголовок кладём на жёлтую плашку во всю ширину.
        # band-duo вдобавок перекрашивает лес — громко и цветно разом.
        base = fit_canvas(bg, w, h)
        if design == "band-duo":
            base = duotone(base, UA_BLUE_DEEP, UA_YELLOW)
        img = veil(base, w, h, 130 if design == "band-duo" else 150)
        img = gradient(img, w, h, int(h * 0.42), 190, top=True)
        img = gradient(img, w, h, int(h * 0.32), 210)
        head_c, kick_c = INK_BLUE, UA_YELLOW
        sub_c, note_c = WARM, L.DIM
    else:
        # Дуотон: лес перекрашен в сине-жёлтое, текст поверх. Вуаль слабее,
        # чем у обычных кадров, — фон здесь половина впечатления.
        img = duotone(fit_canvas(bg, w, h), UA_BLUE_DEEP, UA_YELLOW)
        img = veil(img, w, h, 95)
        img = gradient(img, w, h, int(h * 0.42), 185, top=True)
        img = gradient(img, w, h, int(h * 0.32), 205)
        head_c, kick_c = UA_YELLOW, UA_YELLOW
        sub_c, note_c = WARM, (198, 210, 236)

    d = ImageDraw.Draw(img)
    cx = w // 2

    # Сначала меряем весь блок, потом ставим по оптическому центру: иначе
    # текст липнет к верхнему краю, а половина кадра пустует.
    els = []
    if item.get("kicker"):
        f_k = L.font(L.FONT_SEMI, 36 if story else 32)
        els.append(("k", [" ".join(item["kicker"].upper())], f_k,
                    int(f_k.size * 1.3), kick_c, 34 if story else 26))

    f_h, h_lines = fit_one_line(d, item["headline"], L.FONT_BOLD,
                                156 if story else 140, w - 110,
                                88 if story else 80)
    els.append(("h", h_lines, f_h, int(f_h.size * 1.06), head_c, 30))
    els.append(("rule", [], None, 34, UA_YELLOW, 30))

    if item.get("subline"):
        f_s = L.fit(d, item["subline"], L.FONT_SEMI, 60 if story else 50,
                    w - 170, min_size=34)
        s_lines = L.wrap(d, item["subline"], f_s, w - 170)
        els.append(("s", s_lines, f_s, int(f_s.size * 1.28), sub_c, 20))

    if item.get("note"):
        f_n = L.font(L.FONT_REG, 42 if story else 36)
        n_lines = L.wrap(d, item["note"], f_n, w - 190)
        els.append(("n", n_lines, f_n, int(f_n.size * 1.3), note_c, 0))

    total = sum(len(ln) * lh + after for _, ln, _, lh, _, after in els)
    total += sum(lh for kind, ln, _, lh, _, _ in els if kind == "rule")

    # Центр чуть выше геометрического: снизу футер, и блок должен от него
    # оторваться, а не сесть вплотную
    y = int(h * (0.44 if story else 0.49)) - total // 2

    for kind, lines, fnt, lh, color, after in els:
        if kind == "rule":
            rule(d, cx, y + lh // 2, color=UA_YELLOW)
            y += lh + after
            continue
        if kind == "h" and design in ("band", "band-duo"):
            pad = int(lh * 0.20)
            img.alpha_composite(
                Image.new("RGBA", (w, len(lines) * lh + pad * 2), UA_YELLOW + (255,)),
                (0, y - pad))
            d = ImageDraw.Draw(img)
        band_head = kind == "h" and design in ("band", "band-duo")
        for ln in lines:
            L.shadowed(d, (cx, y + lh // 2), ln, fnt, fill=color,
                       blur=not band_head)
            if kind == "h":
                L.shadowed(d, (cx, y + lh // 2), ln, fnt, fill=color, blur=False)
            y += lh
        y += after

    return footer(img, cfg, w, h, story)


def footer(img, cfg, w, h, story):
    d = ImageDraw.Draw(img)
    f_cta = L.font(L.FONT_BOLD, 42 if story else 38)
    f_disc = L.font(L.FONT_REG, 24 if story else 22)
    cx = w // 2

    y = h - (168 if story else 132)
    L.shadowed(d, (cx, y), cfg["cta"], f_cta, fill=GOLD)

    # Дисклеймер обязателен по закону о диетических добавках — он есть
    # на каждом кадре аккаунта, акционный не исключение
    parts = cfg["disclaimer"].split(". ")
    l1 = ". ".join(parts[:2]) + ("." if len(parts) > 2 else "")
    l2 = ". ".join(parts[2:])
    step = 32 if story else 28
    L.shadowed(d, (cx, y + (60 if story else 48)), l1, f_disc, fill=L.DIM, blur=False)
    if l2:
        L.shadowed(d, (cx, y + (60 if story else 48) + step), l2, f_disc,
                   fill=L.DIM, blur=False)
    return img


# --------------------------------------------------------------------- прогон

def load():
    return yaml.safe_load(PLAN.read_text(encoding="utf-8"))


def gen_backgrounds(plan, force=False):
    """Подложки рисует та же машинка, что и для сторис — 9:16, 2K.

    Пост потом кроппится из вертикали в 4:5: сцены специально спокойные,
    без сюжета по краям, так что вертикальный кроп ничего не режет.
    """
    items = plan["items"]
    if not force:
        items = [i for i in items if not (PENDING / f"{i['id']}_bg.png").exists()]
    if not items:
        print("підкладки вже є (--force щоб перемалювати)")
        return
    PENDING.mkdir(parents=True, exist_ok=True)
    tok = gen.token()
    print(f"малюю підкладки: {len(items)}\n")
    for n, it in enumerate(items):
        gen.generate({**it, "kind": "promo"}, plan["defaults"], tok)
        if n < len(items) - 1:
            time.sleep(gen.PAUSE)


def compose(plan):
    PROMO.mkdir(parents=True, exist_ok=True)
    cfg = plan["defaults"]
    ok = 0
    for it in plan["items"]:
        src = PENDING / f"{it['id']}_bg.png"
        if not src.exists():
            print(f"  ✖ {it['id']}: немає підкладки")
            continue
        w, h = (1080, 1350) if it.get("format") == "post" else (1080, 1920)
        out = render(it, Image.open(src), cfg, w, h).convert("RGB")
        dest = PROMO / f"{it['id']}.jpg"
        out.save(dest, "JPEG", quality=93, optimize=True)
        print(f"  ✔ {it['id']:12} {w}x{h}  {dest.stat().st_size // 1024} KB")
        ok += 1
    print(f"\nзібрано: {ok} із {len(plan['items'])}  →  {PROMO}")


def main() -> int:
    plan = load()
    args = sys.argv[1:]
    do_gen = "--gen" in args or "--compose" not in args
    do_comp = "--compose" in args or "--gen" not in args

    if do_gen:
        gen_backgrounds(plan, force="--force" in args)
    if do_comp:
        compose(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
