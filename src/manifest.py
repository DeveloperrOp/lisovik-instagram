# -*- coding: utf-8 -*-
"""Очередь публикаций.

Очередь лежит ФАЙЛОМ В РЕПОЗИТОРИИ (content/manifest.json), а не в облаке.
Причина простая: организационная политика GCP запрещает создавать ключи
сервисных аккаунтов, поэтому GitHub Actions не может писать в бакет. Зато
он прекрасно коммитит файл обратно в репозиторий — и заодно даёт репозиторию
活ность, из-за отсутствия которой GitHub через 60 дней глушит расписание.

В облаке остаются только медиа: Meta скачивает картинку по прямой ссылке,
и права на запись для этого не нужны.

Статусы элемента:
    approved  — одобрен, ждёт своего окна
    published — ушёл в Instagram
    failed    — попытка не удалась или окно закрылось
    pending   — собран, но ещё не одобрен
    rejected  — забракован
"""
import json
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from config import CONTENT_DIR, GCS_BUCKET

KYIV = ZoneInfo("Europe/Kyiv")
MANIFEST = CONTENT_DIR / "manifest.json"

STATUSES = ("pending", "approved", "published", "rejected", "failed")


def token() -> str:
    """Токен gcloud — нужен только для заливки медиа, локально."""
    return subprocess.run("gcloud auth print-access-token", shell=True,
                          capture_output=True, text=True, check=True).stdout.strip()


def load(tok=None) -> dict:
    """Читает очередь из файла репозитория."""
    if not MANIFEST.exists():
        return {"items": []}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save(manifest: dict, tok=None):
    """Пишет очередь в файл репозитория."""
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")


def upload_media(path, tok=None) -> str:
    """Заливает кадр в GCS и возвращает публичный URL.

    Meta скачивает файл сама, поэтому объект обязан быть доступен снаружи —
    приватная ссылка приведёт к тому, что контейнер зависнет в ERROR.
    Заливка идёт локально, у Actions прав на бакет нет и не нужно.
    """
    name = f"media/{path.name}"
    url = (f"https://storage.googleapis.com/upload/storage/v1/b/{GCS_BUCKET}"
           f"/o?uploadType=media&name={urllib.parse.quote(name, safe='')}")
    ctype = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "video/mp4"
    req = urllib.request.Request(
        url, data=path.read_bytes(),
        headers={"Authorization": f"Bearer {tok or token()}",
                 "Content-Type": ctype},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        r.read()
    return f"https://storage.googleapis.com/{GCS_BUCKET}/{name}"


def slot_window(date: datetime, slot_times: list) -> tuple:
    """Окно публикации в киевском времени.

    Публикуем не в конкретную минуту, а в диапазоне: свет отключают, тревоги,
    да и cron в GitHub Actions опаздывает на 20-60 минут.
    """
    start_h, start_m = map(int, slot_times[0].split(":"))
    end_h, end_m = map(int, slot_times[1].split(":"))
    start = date.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = date.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    return start, end


def add(manifest: dict, story: dict, media_url: str, slot_start: str,
        slot_end: str, kind="STORIES", status="pending") -> dict:
    """Добавляет или обновляет элемент очереди."""
    item = {
        "id": story["id"],
        "kind": kind,
        "theme": story.get("theme", ""),
        "headline": story.get("headline", ""),
        "media_url": media_url,
        "slot_start": slot_start,
        "slot_end": slot_end,
        "status": status,
        "published_at": None,
        "ig_media_id": None,
        "error": None,
    }
    items = [i for i in manifest["items"] if i["id"] != story["id"]]
    items.append(item)
    manifest["items"] = sorted(items, key=lambda i: i["slot_start"])
    return manifest


def due(manifest: dict, now: datetime = None) -> list:
    """Что пора публиковать прямо сейчас.

    Берём одобренное, чьё окно уже открылось и ещё не закрылось.
    Просроченное не публикуем: утренняя сторис вечером никому не нужна.
    """
    now = now or datetime.now(KYIV)
    out = []
    for i in manifest["items"]:
        if i["status"] != "approved":
            continue
        if (datetime.fromisoformat(i["slot_start"]) <= now
                <= datetime.fromisoformat(i["slot_end"])):
            out.append(i)
    return out


def expired(manifest: dict, now: datetime = None) -> list:
    """Одобренное, чьё окно закрылось — публиковать поздно."""
    now = now or datetime.now(KYIV)
    return [i for i in manifest["items"]
            if i["status"] == "approved"
            and datetime.fromisoformat(i["slot_end"]) < now]


def mark(manifest: dict, item_id: str, status: str, **fields) -> dict:
    if status not in STATUSES:
        raise ValueError(f"неизвестный статус: {status}")
    for i in manifest["items"]:
        if i["id"] == item_id:
            i["status"] = status
            i.update(fields)
            break
    return manifest


def stats(manifest: dict) -> dict:
    out = {s: 0 for s in STATUSES}
    for i in manifest["items"]:
        out[i["status"]] = out.get(i["status"], 0) + 1
    return out


if __name__ == "__main__":
    m = load()
    print(f"елементів у черзі: {len(m['items'])}")
    for k, v in stats(m).items():
        if v:
            print(f"  {k}: {v}")
    now = datetime.now(KYIV)
    print(f"\nзараз у Києві: {now:%Y-%m-%d %H:%M}")
    print(f"до публікації зараз: {len(due(m, now))}")
    print(f"прострочено: {len(expired(m, now))}")
