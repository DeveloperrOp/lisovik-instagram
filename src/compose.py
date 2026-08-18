# -*- coding: utf-8 -*-
"""Сборка финальных сторис: подложка + вёрстка по типу.

Вёрстка живёт в layouts.py — там у каждого типа свой макет. Здесь только
подстановка данных и сохранение в формате, который принимает Instagram:
JPEG 1080x1920, до 8 МБ.

    python compose.py              # всё, для чего есть подложка
    python compose.py --week 1
    python compose.py w1-mon-morning
"""
import sys

import yaml
from PIL import Image

import layouts
from config import CONTENT_DIR, OUT_DIR

PLAN = CONTENT_DIR / "content_plan.yaml"
PENDING = OUT_DIR / "pending"


def compose(item: dict, defaults: dict) -> bool:
    src = PENDING / f"{item['id']}_bg.png"
    if not src.exists():
        return False

    bg = Image.open(src)
    try:
        out = layouts.render(item["kind"], bg, item,
                             defaults["cta"], defaults["disclaimer"])
    except Exception as e:
        print(f"  ✖ {item['id']}: {e}")
        return False

    dest = PENDING / f"{item['id']}.jpg"
    out.save(dest, "JPEG", quality=92, optimize=True)
    kb = dest.stat().st_size // 1024
    flag = "  ⚠ больше 8 МБ" if kb > 8000 else ""
    print(f"  ✔ {item['id']} [{item['kind']}] {kb} KB{flag}")
    return True


def main():
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    defaults = plan["defaults"]
    items = plan["stories"]

    args = sys.argv[1:]
    if "--week" in args:
        week = int(args[args.index("--week") + 1])
        items = [i for i in items if i.get("week") == week]
    else:
        ids = {a for a in args if not a.startswith("--")}
        if ids:
            items = [i for i in items if i["id"] in ids]

    ok = sum(compose(i, defaults) for i in items)
    skipped = len(items) - ok
    print(f"\nсобрано: {ok}" + (f" | без подложки: {skipped}" if skipped else ""))


if __name__ == "__main__":
    main()
