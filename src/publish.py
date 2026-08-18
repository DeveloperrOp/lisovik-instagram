# -*- coding: utf-8 -*-
"""Публикация в Instagram через Graph API. Запускается по расписанию в облаке.

Флоу Meta состоит из двух шагов: сначала создаётся контейнер, затем он
публикуется. Между ними контейнер надо дождаться — видео обрабатывается
не мгновенно.

    python publish.py --dry-run    # показать, что было бы опубликовано
    python publish.py              # публиковать по-настоящему

Через API в Stories доступны только голое фото или видео: ни стикера-ссылки,
ни опросов, ни музыки. Это ограничение самой Meta, не наше.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import manifest as mf
from config import GRAPH_VERSION, PROJECT_ROOT


def load_dotenv():
    """Читает .env проекта. В GitHub Actions переменные приходят из секретов,
    локально — из файла; окружение всегда в приоритете."""
    f = PROJECT_ROOT / ".env"
    if not f.exists():
        return
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, _, v = ln.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()
IG_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")

GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"

POLL_TRIES = 30
POLL_WAIT = 5          # сек между проверками готовности контейнера
MAX_PER_RUN = 5        # предохранитель от лавины публикаций при сбое расписания


def api(path: str, params: dict, method="GET") -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    if method == "GET":
        url = f"{GRAPH}/{path}?{data.decode()}"
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"Graph API {e.code}: {body[:300]}") from None


def create_container(item: dict) -> str:
    params = {"access_token": IG_TOKEN}
    if item["kind"] == "REELS":
        params.update({"media_type": "REELS", "video_url": item["media_url"]})
        if item.get("caption"):
            params["caption"] = item["caption"]
    else:
        params.update({"media_type": "STORIES"})
        # У сторис нет caption и alt_text — Meta их не принимает
        if item["media_url"].lower().endswith((".mp4", ".mov")):
            params["video_url"] = item["media_url"]
        else:
            params["image_url"] = item["media_url"]

    r = api(f"{IG_USER_ID}/media", params, "POST")
    return r["id"]


def wait_ready(container_id: str) -> bool:
    """Контейнер обрабатывается асинхронно — фото быстро, видео дольше."""
    for _ in range(POLL_TRIES):
        r = api(container_id, {"fields": "status_code,status",
                               "access_token": IG_TOKEN})
        code = r.get("status_code")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            raise RuntimeError(f"контейнер в ERROR: {r.get('status')}")
        time.sleep(POLL_WAIT)
    raise RuntimeError("контейнер не дошёл до FINISHED")


def publish_item(item: dict) -> str:
    cid = create_container(item)
    wait_ready(cid)
    r = api(f"{IG_USER_ID}/media_publish",
            {"creation_id": cid, "access_token": IG_TOKEN}, "POST")
    return r["id"]


def main() -> int:
    dry = "--dry-run" in sys.argv

    if not dry and (not IG_TOKEN or not IG_USER_ID):
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID в оточенні")
        return 1

    # gcloud тут не нужен: очередь лежит файлом в репозитории, а медиа
    # уже залиты локально при постановке в очередь
    m = mf.load()
    now = datetime.now(mf.KYIV)

    ready = mf.due(m, now)
    stale = mf.expired(m, now)

    print(f"{now:%Y-%m-%d %H:%M} Київ | у черзі {len(m['items'])} | "
          f"до публікації {len(ready)} | прострочено {len(stale)}")

    # Просроченное не публикуем: ранкова сторіс о 22:00 нікому не потрібна
    for i in stale:
        print(f"  ⧗ {i['id']} — вікно зачинилось, пропускаємо")
        mf.mark(m, i["id"], "failed", error="вікно публікації минуло")

    if not ready:
        if stale and not dry:
            mf.save(m)
        print("нічого публікувати")
        return 0

    if len(ready) > MAX_PER_RUN:
        print(f"  ⚠ у черзі {len(ready)}, беремо перші {MAX_PER_RUN}")
        ready = ready[:MAX_PER_RUN]

    published = 0
    for item in ready:
        if dry:
            print(f"  [dry] {item['id']} ({item['kind']}) → {item['media_url']}")
            published += 1
            continue
        try:
            media_id = publish_item(item)
            mf.mark(m, item["id"], "published",
                    published_at=now.isoformat(), ig_media_id=media_id)
            print(f"  ✔ {item['id']} → {media_id}")
            published += 1
        except Exception as e:
            mf.mark(m, item["id"], "failed", error=str(e)[:300])
            print(f"  ✖ {item['id']}: {e}")

    if not dry:
        mf.save(m)
    print(f"\nопубліковано: {published}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
