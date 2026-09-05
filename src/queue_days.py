# -*- coding: utf-8 -*-
"""Постановка днів у чергу в заданому порядку.

queue_week прив'язує продукт до дня тижня: понеділок завжди їжовик,
неділя завжди шиїтаке. Через це старт у неділю відкривав тиждень із
шиїтаке, хоча починати треба з їжовика.

Тут порядок задається явно і кладеться на послідовні дати від старту.
День тижня більше ні на що не впливає — крім оферти, яку підставляє
build_day; вона теж їде разом зі своїм днем.

    python queue_days.py --start 2026-08-30
    python queue_days.py --start 2026-08-30 --order mane,chaga,spirulina
    python queue_days.py --show

Порядок за замовчуванням — від їжовика, як просив власник.
"""
import shutil
import sys
from datetime import datetime, timedelta

import yaml

import manifest as mf
from config import CONTENT_DIR, OUT_DIR

PENDING = OUT_DIR / "pending"
DEFAULTS = CONTENT_DIR / "defaults.yaml"
# Шиїтаке виведено з ротації 31.08.2026 на вимогу власника. Файли днів
# лишились у content, але в публікації не йдуть.
ORDER = ["mane", "chaga", "spirulina", "cordyceps", "ashwagandha", "reishi"]
# Третій набір — не гриби, а чаї й готові курси. Порядок від найширшого
# за попитом продукту до вужчого, щоб тиждень відкривався тим, що бере
# найбільше людей.
ORDER3 = ["osnova", "spokij", "tonus", "sonne", "ivan", "karpaty", "krasa"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def frames(stem: str, prefix="day_") -> list:
    """Кадри одного дня в порядку слотів плюс оферта."""
    path = CONTENT_DIR / f"{prefix}{stem}.yaml"
    items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
    out = [(t["slot"], OUT_DIR / f"{prefix}{stem}" / f"{t['key']}.jpg",
            t.get("topic", "")) for t in items]
    out.append(("night", OUT_DIR / f"{prefix}{stem}" /
            f"{prefix}{stem}-offer.jpg",
                "Лісовик"))
    return out


def main() -> int:
    tok = mf.token()
    m = mf.load(tok)

    if "--show" in sys.argv:
        q = sorted([i for i in m["items"] if i["status"] == "pending"],
                   key=lambda i: i["slot_start"])
        print(f"у черзі: {len(q)}")
        for i in q[:14]:
            print(f"  {i['slot_start'][:16]}  {i['id']}")
        return 0

    slots = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))["slots"]
    prefix = ("day3_" if "--week3" in sys.argv else
              "day2_" if "--week2" in sys.argv else "day_")
    order = (arg("--order") or ",".join(
        ORDER3 if "--week3" in sys.argv else ORDER)).split(",")
    start = datetime.fromisoformat(
        arg("--start") or datetime.now(mf.KYIV).strftime("%Y-%m-%d"))
    start = start.replace(tzinfo=mf.KYIV)
    now = datetime.now(mf.KYIV)

    # Свіжий запуск не має спотикатись об уже поставлені кадри: старі
    # approved прибираємо, опубліковані лишаємо недоторканими.
    m["items"] = [i for i in m["items"] if i["status"] != "pending"]
    PENDING.mkdir(parents=True, exist_ok=True)

    queued = late = 0
    for n, stem in enumerate(order):
        date = start + timedelta(days=n)
        for slot, src, topic in frames(stem, prefix):
            if not src.exists():
                print(f"  ✖ {stem}/{slot}: немає файлу")
                continue
            sid = f"{date:%m%d}-{stem}-{slot}"
            w_start, w_end = mf.slot_window(date, slots[slot])
            if w_end < now:
                late += 1
                continue
            shutil.copy2(src, PENDING / f"{sid}.jpg")
            url = mf.upload_media(PENDING / f"{sid}.jpg", tok)
            # status ОБОВʼЯЗКОВО передається явно. У mf.add за
            # замовчуванням стоїть «pending» — стан для ручного схвалення
            # через бота, а due() бере ТІЛЬКИ «approved». Саме через
            # пропущений тут параметр черга 30.08 не публікувалась узагалі,
            # тоді як queue_week.py працював: він передає його рядком 126.
            mf.add(m, {"id": sid, "theme": topic, "kind": "story"}, url,
                   w_start.isoformat(), w_end.isoformat(),
                   status="approved")
            print(f"  ✔ {w_start:%d.%m %H:%M}  {sid:26} {topic}")
            queued += 1

    mf.save(m, tok)
    print(f"\nу черзі: {queued}" + (f" | вікно вже минуло: {late}" if late else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
