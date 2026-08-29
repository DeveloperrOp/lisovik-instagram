# -*- coding: utf-8 -*-
"""Мост от файлов дня к очереди публикации.

queue_week.py и publish.py уже работают и проверены: они берут план из
content_plan.yaml и файлы из out/pending. Переписывать их под новый формат
незачем — дешевле собрать план из day_*.yaml и разложить кадры.

Что делает:
  1. читает все content/day_*.yaml плюс оферту дня из offers.yaml
  2. складывает кадры в out/pending под id вида w1-mon-dawn
  3. пишет content_plan.yaml, который понимает queue_week

    python plan_from_days.py            # показать, что соберётся
    python plan_from_days.py --write    # собрать

Кадр без готового jpg в план не попадает: публиковать нечего, и лучше
увидеть это здесь, чем пустое окно в очереди.
"""
import shutil
import sys


def arg(name, default=None):
    return (sys.argv[sys.argv.index(name) + 1]
            if name in sys.argv else default)

import yaml

from config import CONTENT_DIR, OUT_DIR

PENDING = OUT_DIR / "pending"
PLAN = CONTENT_DIR / "content_plan.yaml"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def rows(week=1) -> list:
    offers = {o["day"]: o for o in yaml.safe_load(
        (CONTENT_DIR / "offers.yaml").read_text(encoding="utf-8"))["offers"]}
    out = []
    for path in sorted(CONTENT_DIR.glob("day_*.yaml")):
        items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        if not items:
            continue
        day = items[0].get("day")
        src = OUT_DIR / path.stem
        frames = [(t["slot"], t["key"], t.get("topic", "")) for t in items]
        if day in offers:
            frames.append(("night", f"{path.stem}-offer", "Лісовик"))
        for slot, key, topic in frames:
            out.append({"id": f"w{week}-{day}-{slot}",
                        "week": week, "day": day, "slot": slot,
                        "kind": "offer" if slot in ("night", "sell") else "useful",
                        "mode": "auto",
                        "theme": topic,
                        "src": src / f"{key}.jpg"})
    out.sort(key=lambda r: (DAYS.index(r["day"]), r["slot"]))
    return out


def main() -> int:
    write = "--write" in sys.argv
    # Кілька тижнів одразу: завтрашній день іде «хвостом» поточного
    # тижня, а повний цикл стартує з понеділка. Id у них різні, тому в
    # черзі вони не сплутаються.
    weeks = [int(x) for x in (arg("--weeks", "1") or "1").split(",")]
    data = [r for w in weeks for r in rows(w)]
    ready = [r for r in data if r["src"].exists()]
    missing = [r for r in data if not r["src"].exists()]

    for r in data:
        mark = "є" if r["src"].exists() else "НЕМАЄ"
        print(f"  {r['id']:16} {mark:6} {r['theme'][:22]:24} {r['src'].name}")
    print(f"\nготових кадрів: {len(ready)} із {len(data)}")
    if missing:
        print("без файлу:", ", ".join(r["id"] for r in missing))
    if not write:
        print("\nце перегляд. Щоб зібрати: --write")
        return 0

    PENDING.mkdir(parents=True, exist_ok=True)
    for r in ready:
        shutil.copy2(r["src"], PENDING / f"{r['id']}.jpg")

    plan = {"meta": {"weeks": 1, "lang": "ua",
                     "structure": "день = один продукт, 6 кадрів"},
            "stories": [{k: r[k] for k in
                         ("id", "week", "day", "slot", "kind", "mode", "theme")}
                        for r in ready]}
    PLAN.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")
    print(f"\nсклав план: {PLAN}")
    print(f"кадри в черзі: {PENDING}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
