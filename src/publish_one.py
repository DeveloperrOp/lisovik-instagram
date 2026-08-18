# -*- coding: utf-8 -*-
"""Публикация одной сторис — для проверки связки и разовых публикаций.

    python publish_one.py w1-mon-morning
    python publish_one.py w1-mon-morning --dry-run

Флоу Meta: залить медиа в публичный бакет -> создать контейнер
(media_type=STORIES) -> дождаться FINISHED -> media_publish.
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from config import GRAPH_VERSION, PROJECT_ROOT, OUT_DIR

GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"
PENDING = OUT_DIR / "pending"


def load_dotenv():
    p = PROJECT_ROOT / ".env"
    if not p.exists():
        return
    for ln in p.read_text(encoding="utf-8").splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, _, v = ln.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def api(path: str, params: dict, method="GET") -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    if method == "GET":
        req = urllib.request.Request(f"{GRAPH}/{path}?{data.decode()}")
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"Graph API {e.code}: {body[:300]}") from None


def upload(path: pathlib.Path, bucket: str) -> str:
    """Заливает кадр в GCS. Meta скачивает файл сама, ссылка должна быть публичной."""
    dest = f"gs://{bucket}/media/{path.name}"
    subprocess.run(f'gcloud storage cp "{path}" {dest}', shell=True,
                   check=True, capture_output=True)
    return f"https://storage.googleapis.com/{bucket}/media/{path.name}"


def main() -> int:
    load_dotenv()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        print("укажи id, напр.: python publish_one.py w1-mon-morning")
        return 1

    sid = args[0]
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    ig_id = os.environ.get("IG_USER_ID", "")
    bucket = os.environ.get("LISOVIK_BUCKET", "")
    if not all((token, ig_id, bucket)):
        print("не заповнений .env")
        return 1

    src = PENDING / f"{sid}.jpg"
    if not src.exists():
        print(f"нема файлу {src}")
        return 1

    print(f"кадр: {src.name} ({src.stat().st_size // 1024} KB)")

    url = upload(src, bucket)
    print(f"завантажено: {url}")

    with urllib.request.urlopen(url, timeout=60) as r:
        print(f"перевірка доступності: HTTP {r.status}")

    if dry:
        print("\n[dry-run] далі був би контейнер і публікація")
        return 0

    print("\nстворюю контейнер...")
    cont = api(f"{ig_id}/media",
               {"media_type": "STORIES", "image_url": url,
                "access_token": token}, "POST")
    cid = cont["id"]
    print(f"  контейнер {cid}")

    for i in range(30):
        st = api(cid, {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            print("  готовий до публікації")
            break
        if code == "ERROR":
            print(f"  ✖ помилка обробки: {st.get('status')}")
            return 1
        time.sleep(4)
    else:
        print("  ✖ не дочекались FINISHED")
        return 1

    print("публікую...")
    res = api(f"{ig_id}/media_publish",
              {"creation_id": cid, "access_token": token}, "POST")
    media_id = res["id"]
    print(f"\n✅ опубліковано! media_id = {media_id}")

    info = api(media_id, {"fields": "media_type,media_product_type,timestamp,permalink",
                          "access_token": token})
    for k, v in info.items():
        if k != "id":
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
