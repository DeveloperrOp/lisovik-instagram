# -*- coding: utf-8 -*-
"""Готові кадри тижня — в окрему чисту теку «ГОТОВІ СТОРІС/тиждень-N».

out/ — робоча тека: підкладки, _chk, _blank, _rej і ще сотня тек
попередніх тижнів. Ярик 19.10: «я просил делать отдельно без мусора в
отдельной папочке, удобно для работы». Тому сюди йдуть тільки фінальні
кадри, одна плоска тека, імена сортуються в порядку виходу — як у
тиждень-1:

    1-Вт_Їжовик_07-00_факт.jpg
    1-Вт_Їжовик_19-00_ТОВАР.jpg

Порядок днів і кадрів — той самий, що в черзі (queue_days.frames).

    python export_ready.py --week9 --start 2026-10-20
"""
import shutil
import sys
from datetime import datetime, timedelta

import yaml

import queue_days as Q
from config import CONTENT_DIR, PROJECT_ROOT

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
KIND = {"dawn": "факт", "morning": "факт", "noon": "факт", "evening": "факт",
        "sell": "ТОВАР", "night": "форми"}


def main() -> int:
    n = next((a[6:] for a in sys.argv if a.startswith("--week")), None)
    if not n or "--start" not in sys.argv:
        print("python export_ready.py --week9 --start 2026-10-20")
        return 1
    order = getattr(Q, f"ORDER{n}")
    start = datetime.fromisoformat(Q.arg("--start"))
    slots = yaml.safe_load((CONTENT_DIR / "defaults.yaml")
                           .read_text(encoding="utf-8"))["slots"]

    dest = PROJECT_ROOT / "ГОТОВІ СТОРІС" / f"тиждень-{n}"
    # Тека перезбирається з нуля: якщо кадр перегенерували, стара версія
    # не має лишитись поруч із новою.
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    copied = 0
    for i, stem in enumerate(order):
        day = DAYS[(start + timedelta(days=i)).weekday()]
        frames = Q.frames(stem, f"day{n}_")
        name = (frames[0][2] or stem).split()[0]
        for slot, src, _ in frames:
            if not src.exists():
                print(f"  ✖ немає {src}")
                continue
            hhmm = slots[slot][0].replace(":", "-")
            shutil.copy2(src, dest / f"{i + 1}-{day}_{name}_{hhmm}_"
                                     f"{KIND.get(slot, slot)}.jpg")
            copied += 1

    overview = PROJECT_ROOT / "out" / f"week{n}_overview.jpg"
    if overview.exists():
        shutil.copy2(overview, dest / "0_огляд-тижня.jpg")
    print(f"кадрів: {copied} → {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
