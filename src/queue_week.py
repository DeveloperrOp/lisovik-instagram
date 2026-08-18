# -*- coding: utf-8 -*-
"""Постановка одобренных кадров в очередь публикации.

Заливает медиа в GCS и пишет манифест с расписанием: каждому кадру —
своё окно по дню недели и слоту из defaults.yaml.

    python queue_week.py --week 1                     # с ближайшего понедельника
    python queue_week.py --week 1 --start 2026-08-24  # с конкретной даты
    python queue_week.py --week 1 --skip w1-tue-night,w1-sat-day
    python queue_week.py --show                       # что уже в очереди

Публикуется потом само — publish.py берёт из этой очереди то, чьё окно открыто.
"""
import sys
from datetime import datetime, timedelta

import yaml

import manifest as mf
from config import CONTENT_DIR, OUT_DIR

PLAN = CONTENT_DIR / "content_plan.yaml"
DEFAULTS = CONTENT_DIR / "defaults.yaml"
PENDING = OUT_DIR / "pending"

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def show():
    m = mf.load()
    items = m.get("items", [])
    if not items:
        print("черга порожня")
        return
    print(f"у черзі: {len(items)}\n")
    for i in sorted(items, key=lambda x: x["slot_start"]):
        start = datetime.fromisoformat(i["slot_start"])
        mark = {"approved": "•", "published": "✔", "failed": "✖",
                "pending": "…", "rejected": "—"}.get(i["status"], "?")
        print(f"  {mark} {start:%d.%m %H:%M}  {i['id']:22} {i['status']:9} "
              f"{i.get('headline','')[:34]}")
    print()
    for k, v in mf.stats(m).items():
        if v:
            print(f"  {k}: {v}")


def main() -> int:
    if "--show" in sys.argv:
        show()
        return 0

    week = int(arg("--week", "1"))
    skip = {s.strip() for s in (arg("--skip", "") or "").split(",") if s.strip()}
    manual_too = "--with-manual" in sys.argv
    catch_up = "--catch-up" in sys.argv
    catch_idx = [0]
    now = datetime.now(mf.KYIV)

    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    defaults = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
    slots = defaults["slots"]

    start_arg = arg("--start")
    if start_arg:
        start = datetime.fromisoformat(start_arg).replace(tzinfo=mf.KYIV)
    else:
        # ближайший будущий понедельник
        today = datetime.now(mf.KYIV).replace(hour=0, minute=0, second=0, microsecond=0)
        start = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    print(f"тиждень {week}, старт {start:%d.%m.%Y} (понеділок)\n")

    items = [s for s in plan["stories"] if s.get("week") == week]
    tok = mf.token()
    m = mf.load(tok)
    queued = skipped = 0

    for s in items:
        sid = s["id"]
        if sid in skip:
            print(f"  — {sid}: пропущено вручну")
            skipped += 1
            continue
        # Кадри зі стікером публікуються руками — в чергу не ставимо
        if s.get("mode") == "manual" and not manual_too:
            print(f"  — {sid}: {s['kind']}, публікується руками")
            skipped += 1
            continue

        src = PENDING / f"{sid}.jpg"
        if not src.exists():
            print(f"  ✖ {sid}: немає файлу")
            skipped += 1
            continue

        date = start + timedelta(days=DAYS.index(s["day"]))
        w_start, w_end = mf.slot_window(date, slots[s["slot"]])

        # Стартуємо серед дня: слоти, що вже минули сьогодні, не викидаємо,
        # а ставимо на найближчі хвилини з розбіжкою — інакше перший день
        # вийде наполовину порожнім.
        if catch_up and w_end < now:
            w_start = now + timedelta(minutes=2 + catch_idx[0] * 4)
            w_end = w_start + timedelta(minutes=90)
            catch_idx[0] += 1

        url = mf.upload_media(src, tok)
        mf.add(m, s, url, w_start.isoformat(), w_end.isoformat(),
               status="approved")
        print(f"  ✔ {w_start:%d.%m %H:%M}  {sid:22} {s.get('headline','')[:30]}")
        queued += 1

    mf.save(m, tok)
    print(f"\nу черзі: {queued} | пропущено: {skipped}")
    print("публікація піде сама, коли відкриється вікно кожного кадру")
    return 0


if __name__ == "__main__":
    sys.exit(main())
