# -*- coding: utf-8 -*-
"""Тесты логики очереди публикаций. Запуск: python test_manifest.py

Публикатор крутится в облаке без присмотра, поэтому логика окон должна быть
проверена локально: опубликовать ранкову сторіс о 22:00 хуже, чем не
опубликовать вовсе.
"""
import sys
from datetime import datetime, timedelta

import manifest as mf

KYIV = mf.KYIV


def item(iid, status, start, end):
    return {"id": iid, "kind": "STORIES", "rubric": "test", "headline": "",
            "media_url": f"https://example.com/{iid}.jpg",
            "slot_start": start.isoformat(), "slot_end": end.isoformat(),
            "status": status, "published_at": None, "ig_media_id": None,
            "error": None}


def main() -> int:
    now = datetime(2026, 8, 20, 10, 0, tzinfo=KYIV)
    failures = []

    def check(name, got, expected):
        if got != expected:
            failures.append(f"{name}: очікували {expected}, отримали {got}")

    m = {"items": [
        # окно открыто прямо сейчас
        item("now-open", "approved", now - timedelta(minutes=30),
             now + timedelta(minutes=60)),
        # окно ещё не наступило
        item("future", "approved", now + timedelta(hours=3),
             now + timedelta(hours=4)),
        # окно закрылось час назад
        item("stale", "approved", now - timedelta(hours=3),
             now - timedelta(hours=1)),
        # в окне, но не одобрено — публиковать нельзя
        item("pending-in-window", "pending", now - timedelta(minutes=10),
             now + timedelta(minutes=50)),
        # уже опубликовано — второй раз не публикуем
        item("done", "published", now - timedelta(minutes=20),
             now + timedelta(minutes=40)),
        # забраковано на ревью
        item("rejected", "rejected", now - timedelta(minutes=5),
             now + timedelta(minutes=55)),
    ]}

    due = [i["id"] for i in mf.due(m, now)]
    check("due", due, ["now-open"])

    expired = [i["id"] for i in mf.expired(m, now)]
    check("expired", expired, ["stale"])

    # границы окна включительно
    edge = {"items": [item("edge-start", "approved", now, now + timedelta(hours=1)),
                      item("edge-end", "approved", now - timedelta(hours=1), now)]}
    check("границы окна", sorted(i["id"] for i in mf.due(edge, now)),
          ["edge-end", "edge-start"])

    # смена статуса
    mf.mark(m, "now-open", "published", ig_media_id="123")
    got = next(i for i in m["items"] if i["id"] == "now-open")
    check("mark.status", got["status"], "published")
    check("mark.ig_media_id", got["ig_media_id"], "123")
    check("после публикации не в очереди", [i["id"] for i in mf.due(m, now)], [])

    # неизвестный статус должен падать, а не тихо записываться
    try:
        mf.mark(m, "future", "whatever")
        failures.append("mark: неизвестный статус не вызвал ошибку")
    except ValueError:
        pass

    # окно слота из defaults
    start, end = mf.slot_window(now, ["09:30", "11:00"])
    check("slot_window.start", f"{start:%H:%M}", "09:30")
    check("slot_window.end", f"{end:%H:%M}", "11:00")

    # статистика
    s = mf.stats(m)
    check("stats.published", s["published"], 2)
    check("stats.rejected", s["rejected"], 1)

    for f in failures:
        print(f"  ✖ {f}")
    print(f"\nпровалів: {len(failures)}")
    if failures:
        return 1
    print("✅ логіка черги коректна")
    return 0


if __name__ == "__main__":
    sys.exit(main())
