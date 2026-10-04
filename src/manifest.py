# -*- coding: utf-8 -*-
"""Очередь публикаций.

Очередь лежит ФАЙЛОМ В РЕПОЗИТОРИИ (content/manifest.json), а не в облаке.
Причина простая: организационная политика GCP запрещает создавать ключи
сервисных аккаунтов, поэтому GitHub Actions не может писать в бакет. Зато
он прекрасно коммитит файл обратно в репозиторий — и заодно даёт репозиторию
活ность, из-за отсутствия которой GitHub через 60 дней глушит расписание.

Медиа лежат ТАМ ЖЕ, в репозитории: Meta скачивает картинку по прямой
ссылке, и raw.githubusercontent отдаёт её с правильным image/jpeg.

Раньше медиа жили в бакете GCS. 04.10.2026 проект GCP оказался помечен
на удаление — бакет исчез, и публикации встали: Meta получала по ссылке
404 и отвечала «Only photo or video can be accepted». Девять кадров
сгорело, пока это не всплыло. Теперь публикация не зависит от облака
вообще: репозиторий публичный, и этого достаточно.

Статусы элемента:
    approved  — одобрен, ждёт своего окна
    published — ушёл в Instagram
    failed    — попытка не удалась или окно закрылось
    pending   — собран, но ещё не одобрен
    rejected  — забракован
"""
import json
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from config import CONTENT_DIR

KYIV = ZoneInfo("Europe/Kyiv")
MANIFEST = CONTENT_DIR / "manifest.json"
MEDIA = CONTENT_DIR.parent / "media"
GH_RAW = ("https://raw.githubusercontent.com/DeveloperrOp/"
          "lisovik-instagram/master/media/")

STATUSES = ("pending", "approved", "published", "rejected", "failed")


def token() -> str:
    """Больше не нужен: медиа раздаёт GitHub, а не бакет.

    Оставлен как заглушка, потому что его зовут восемь скриптов. Когда
    gcloud в системе есть, вернёт настоящий токен; когда нет — пустую
    строку, и это ничего не ломает.
    """
    try:
        return subprocess.run("gcloud auth print-access-token", shell=True,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return ""


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


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(CONTENT_DIR.parent),
                          capture_output=True, text=True)


def flush_media() -> None:
    """Отправляет накопленные кадры на сервер.

    Пока файла нет на GitHub, ссылка на него — просто текст: Meta придёт
    и получит 404.
    """
    if not _git("diff", "--cached", "--quiet").returncode:
        return                      # нечего отправлять
    _git("commit", "-q", "-m", "медіа: кадри для публікації")
    r = _git("push", "-q")
    if r.returncode:
        raise RuntimeError("медіа не відправлені на GitHub: "
                           + (r.stderr or r.stdout).strip()[:200])


def media_ready(url: str, tries: int = 10) -> bool:
    """Чекает, пока ссылка реально начнёт отдавать файл."""
    for n in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def upload_media(path, tok=None, push=True) -> str:
    """Кладёт кадр в репозиторий и возвращает публичную ссылку на него.

    Meta скачивает файл сама, поэтому он обязан быть доступен снаружи.
    raw.githubusercontent отдаёт .jpg с Content-Type: image/jpeg — это
    ровно то, что требует Graph API.

    Кириллица в имени — отдельная ловушка Graph API (ошибка 9004), но
    имена кадров у нас латиницей, и переименовывать нечего.

    push=False нужен тем, кто заливает пачку: тогда файлы только
    добавляются в индекс, а отправляет их один flush_media() в конце.
    """
    MEDIA.mkdir(parents=True, exist_ok=True)
    dst = MEDIA / path.name
    if not dst.exists() or dst.read_bytes() != path.read_bytes():
        shutil.copy2(path, dst)
    _git("add", str(dst))
    url = GH_RAW + urllib.parse.quote(path.name)
    if push:
        flush_media()
        if not media_ready(url):
            raise RuntimeError(f"кадр не роздається за посиланням: {url}")
    return url


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
