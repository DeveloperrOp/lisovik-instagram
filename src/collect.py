# -*- coding: utf-8 -*-
"""Сборка всего готового в одну папку для просмотра.

Ярик: «сделай мне общую папку, чтобы удобно было глянуть».

Раскладывает кадры по дням недели в порядке публикации и называет файлы
временем слота — тогда порядок виден в проводнике без открывания. Плюс
лист всей недели одной картинкой.

Копии, а не оригиналы: папка собирается заново каждый раз и её можно
удалять без потерь.

    python collect.py
"""
import shutil
import sys

import yaml
from PIL import Image, ImageDraw

from config import CONTENT_DIR, OUT_DIR

import sys as _s
DEST = OUT_DIR / ("ГОТОВЕ-3" if "--week3" in _s.argv else
                  "ГОТОВЕ-2" if "--week2" in _s.argv else "ГОТОВЕ")
DAYS = [("mon", "1-ПН"), ("tue", "2-ВТ"), ("wed", "3-СР"), ("thu", "4-ЧТ"),
        ("fri", "5-ПТ"), ("sat", "6-СБ"), ("sun", "7-НД")]


def day_files(prefix="day_") -> dict:
    """Какому дню какой файл соответствует."""
    out = {}
    for path in sorted(CONTENT_DIR.glob(f"{prefix}*.yaml")):
        items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        if items:
            out[items[0].get("day")] = path
    return out


def main() -> int:
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    slots = yaml.safe_load(
        (CONTENT_DIR / "defaults.yaml").read_text(encoding="utf-8"))["slots"]
    prefix = ("day3_" if "--week3" in sys.argv else
              "day2_" if "--week2" in sys.argv else "day_")
    files = day_files(prefix)
    sheets, missing = [], []

    for day, label in DAYS:
        path = files.get(day)
        if not path:
            missing.append(f"{label}: немає файлу дня")
            continue
        items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        src = OUT_DIR / path.stem
        topic = items[0].get("topic", "?")
        folder = DEST / f"{label}-{topic}"
        folder.mkdir()

        # оферта подставляется сборщиком, в файле дня её нет
        order = [(t["slot"], t["key"]) for t in items]
        order.append(("night", f"{path.stem}-offer"))
        order.sort(key=lambda x: list(slots).index(x[0]))

        for slot, key in order:
            jpg = src / f"{key}.jpg"
            if not jpg.exists():
                missing.append(f"{label} {slots[slot][0]} — {key}")
                continue
            shutil.copy2(jpg, folder / f"{slots[slot][0].replace(':', '-')}"
                                       f"_{key}.jpg")
        sheet = src / "_day.jpg"
        if sheet.exists():
            shutil.copy2(sheet, DEST / f"{label}-{topic}.jpg")
            sheets.append((f"{label} {topic}", Image.open(sheet)))

    if sheets:
        tw = 1100
        th = [im.resize((tw, int(tw * im.height / im.width)))
              for _, im in sheets]
        h = max(i.height for i in th)
        page = Image.new("RGB", (tw + 24, sum(i.height + 34 for i in th) + 10),
                         (24, 24, 26))
        d = ImageDraw.Draw(page)
        y = 8
        for (name, _), im in zip(sheets, th):
            d.text((14, y + 6), name, fill=(240, 200, 60))
            page.paste(im, (12, y + 26))
            y += im.height + 34
        page.save(DEST / "0_ТИЖДЕНЬ.jpg", "JPEG", quality=88)

    print(f"зібрано днів: {len(sheets)} із 7  →  {DEST}")
    if missing:
        print("\nне вистачає кадрів:")
        for m in missing:
            print("   ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
