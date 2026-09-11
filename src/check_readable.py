# -*- coding: utf-8 -*-
"""Чи читається текст на кадрі — рахунок, а не «на око».

Ярик 11.09: «дивись, щоб текст скрізь був читабельним». На кадрах, де текст
лягає поверх фотографії, це не питання смаку: літера на світлій банці або на
темному листку просто зникає, і видно це аж на опублікованому пості.

Механіка проста і не залежить від розкладки:

  1. беремо кадр і його підкладку (той самий фон без тексту);
  2. пікселі, які відрізняються, — це і є літери (еталон готується
     тим самим рендером із прихованим текстом, тому збіг піксельний);
  3. для кожного такого пікселя дивимось, ЩО лежить під ним на підкладці;
  4. рахуємо контраст за WCAG між кольором літери й тим, що під нею.

Контраст нижче 3.0 означає, що навіть великий текст тут не читається.
Скрипт повертає частку таких пікселів і найгіршу ділянку кадру.

    python check_readable.py ../out/post_blot
"""
import sys
from pathlib import Path

from PIL import Image

# WCAG дає 4.5 для дрібного тексту й 3.0 для великого. У нас увесь текст
# на кадрі великий — від 25px, заголовки під 80px, — тому поріг 3.0.
# Наш фірмовий оливковий на білому папері дає 3.8: за суворішим порогом
# у брак летіли б і зразкові пости Лісовика.
MIN_CONTRAST = 3.0
MAX_BAD_SHARE = 0.04        # понад 4% проблемних пікселів — кадр бракуємо
DIFF = 70                   # тільки щільні пікселі літери, без згладжених країв

# Кольори, якими ми набираємо текст. Контраст рахуємо не з тим, що вийшло
# на краю літери після згладжування, а з ЗАДАНИМ кольором: питання ж у
# тому, чи читається літера на цьому фоні, а не який у неї контур.
INKS = [(123, 129, 43),     # оливковий заголовок
        (43, 58, 92),       # синій підзаголовок
        (168, 85, 44),      # теракотовий акцент
        (47, 49, 40),       # основний текст
        (92, 95, 82)]       # сірий підпис


def nearest_ink(px):
    return min(INKS, key=lambda c: (c[0] - px[0]) ** 2 + (c[1] - px[1]) ** 2
               + (c[2] - px[2]) ** 2)


def lum(px) -> float:
    """Відносна яскравість за WCAG."""
    c = []
    for v in px[:3]:
        v /= 255.0
        c.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b) -> float:
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check(frame: Path, bg: Path, step=2):
    fi = Image.open(frame).convert("RGB")
    bi = Image.open(bg).convert("RGB").resize(fi.size)
    fp, bp = fi.load(), bi.load()
    W, H = fi.size

    total = bad = 0
    worst = None
    # кадр ділимо на клітинки, щоб показати, ДЕ саме проблема
    cells = {}
    for y in range(0, H, step):
        for x in range(0, W, step):
            f, b = fp[x, y], bp[x, y]
            if abs(f[0] - b[0]) + abs(f[1] - b[1]) + abs(f[2] - b[2]) < DIFF:
                continue
            total += 1
            c = contrast(nearest_ink(f), b)
            key = (int(y / H * 6), int(x / W * 4))
            cell = cells.setdefault(key, [0, 0])
            cell[0] += 1
            if c < MIN_CONTRAST:
                bad += 1
                cell[1] += 1
                if worst is None or c < worst[0]:
                    worst = (c, x, y)
    if not total:
        return {"letters": 0, "bad": 0.0, "worst": None, "cells": []}
    hot = sorted(((v[1] / v[0], k) for k, v in cells.items() if v[0] > 40),
                 reverse=True)[:3]
    return {"letters": total, "bad": bad / total,
            "worst": None if worst is None else round(worst[0], 2),
            "cells": [(f"рядок {k[0] + 1}/6, колонка {k[1] + 1}/4",
                       round(share, 2)) for share, k in hot if share > 0.02]}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "../out/post_blot")
    frames = sorted(p for p in root.glob("*.png")
                    if not p.stem.startswith(("bg_", "0_")))
    if not frames:
        print("немає кадрів у", root)
        return 1
    worst_frames = []
    for f in frames:
        bg = f.parent / "_blank" / f.name
        if not bg.exists():
            print(f"  ? {f.stem}: немає підкладки, пропускаю")
            continue
        r = check(f, bg)
        mark = "✔" if r["bad"] <= MAX_BAD_SHARE else "✖"
        print(f"  {mark} {f.stem:22} літер-пікселів {r['letters']:6} | "
              f"нечитабельних {r['bad'] * 100:5.1f}% | найгірший контраст "
              f"{r['worst']}")
        for where, share in r["cells"]:
            print(f"        · {where}: {share * 100:.0f}% проблемних")
        if r["bad"] > MAX_BAD_SHARE:
            worst_frames.append(f.stem)
    print()
    if worst_frames:
        print("переробити:", ", ".join(worst_frames))
        return 1
    print("текст читається на всіх кадрах")
    return 0


if __name__ == "__main__":
    sys.exit(main())
