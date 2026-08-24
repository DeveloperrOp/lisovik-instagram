# -*- coding: utf-8 -*-
"""Генерация подложек для сторис через Vertex AI.

Два режима, по типу кадра:
  product — реальное фото товара идёт референсом, модель обязана сохранить
            банку и этикетку и только переносит её в сцену; заголовок
            рисует сама (в 2K украинский держится)
  всё остальное — чистый фон БЕЗ текста, надписи потом положит PIL

    python generate.py --week 1
    python generate.py w1-mon-morning
    python generate.py --week 1 --force     # перерисовать уже готовое
"""
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

import yaml

import theme
from config import (CONTENT_DIR, GCP_LOCATION, GCP_PROJECT, IMAGE_MODEL,
                    IMAGE_SIZE, OUT_DIR)

PLAN = CONTENT_DIR / "content_plan.yaml"
PENDING = OUT_DIR / "pending"
PHOTOS = OUT_DIR / "photos"

RETRIES = 6
BACKOFF = 25
PAUSE = 10

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

PRODUCT_PROMPT = """Vertical 9:16 product photograph for a Ukrainian wellness brand.

The attached image is MY REAL PRODUCT. Keep this exact package: identical
shape, identical label artwork, identical logo, identical Ukrainian wording
on the label. Do not redesign it, do not invent packaging, do not change
any letters or numbers on the label.

Place it standing naturally in this scene: {scene}
Overall look and light of the shot: {style}
Keep the product itself untouched — the look above applies to the setting,
the light and the colour of the scene, never to the package.
Setting stays TEMPERATE and UKRAINIAN — no tropical plants, no palms,
no jungle.

The product sits in the LOWER HALF and is clearly the hero.
The upper third stays empty and calm — headline goes there later.

Render NO TEXT of your own anywhere in the frame: no headline, no caption,
no light panel or box for text. The only readable words in the picture are
the ones already printed on the product label.

MUST NOT CONTAIN: {negative}
"""

SCENE_PROMPT = """Vertical 9:16 background plate for an Instagram Story.

Scene: {scene}
Style: {style}

This is a BACKGROUND ONLY. Large text will be placed on top of it later,
so keep the composition calm, without a strong focal point in the middle.

Render NO TEXT AT ALL anywhere in the image: no letters, no numbers,
no labels, no signage.

MUST NOT CONTAIN: {negative}
"""


def token() -> str:
    """Токен активного gcloud-логина.

    ADC на машине принадлежит другому аккаунту с quota-проектом, где Vertex
    выключен, поэтому берём токен напрямую у gcloud.
    """
    return subprocess.run("gcloud auth print-access-token", shell=True,
                          capture_output=True, text=True, check=True).stdout.strip()


def fetch_photo(url: str, article: str):
    """Скачивает фото товара с сайта. Перед ним Cloudflare — нужен UA браузера."""
    PHOTOS.mkdir(parents=True, exist_ok=True)
    dest = PHOTOS / f"{article}.jpg"
    if dest.exists():
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    try:
        dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        return dest
    except Exception as e:
        print(f"    ✖ фото не скачалось: {e}")
        return None


def scene_style(item: dict, defaults: dict) -> str:
    """Стиль сцены — из вайба недели. У разовых кадров недели нет."""
    if item.get("week"):
        try:
            return theme.for_week(item["week"])["style"].strip()
        except Exception as e:
            print(f"    ⚠ тема тижня {item['week']} не зчиталась ({e}), беру базовий стиль")
    return defaults["style"].strip()


def build_parts(item: dict, defaults: dict):
    neg = defaults["negative"].strip()
    if item["kind"] == "product" and item.get("photo_url"):
        photo = fetch_photo(item["photo_url"], item.get("article", item["id"]))
        if photo:
            return [
                {"inlineData": {"mimeType": "image/jpeg",
                                "data": base64.b64encode(photo.read_bytes()).decode()}},
                {"text": PRODUCT_PROMPT.format(
                    scene=item["scene"], style=scene_style(item, defaults),
                    headline=item["headline"],
                    subline=item.get("subline", ""), negative=neg)},
            ]
    return [{"text": SCENE_PROMPT.format(
        scene=item["scene"], style=scene_style(item, defaults),
        negative=neg)}]


def generate(item: dict, defaults: dict, tok: str) -> bool:
    host = ("aiplatform.googleapis.com" if GCP_LOCATION == "global"
            else f"{GCP_LOCATION}-aiplatform.googleapis.com")
    url = (f"https://{host}/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
           f"/publishers/google/models/{IMAGE_MODEL}:generateContent")

    body = {
        "contents": [{"role": "user", "parts": build_parts(item, defaults)}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "9:16", "imageSize": IMAGE_SIZE},
        },
    }

    data = None
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {tok}",
                     "X-Goog-User-Project": GCP_PROJECT,
                     "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=420) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            # 429 при пачечной генерации в 2K — обычное дело
            if e.code in (429, 500, 503) and attempt < RETRIES:
                wait = BACKOFF * attempt
                print(f"    … HTTP {e.code}, повтор через {wait}s")
                time.sleep(wait)
                continue
            print(f"  ✖ {item['id']}: HTTP {e.code} {e.read()[:150]}")
            return False
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            # обрыв связи не должен ронять всю пачку
            if attempt < RETRIES:
                wait = BACKOFF * attempt
                print(f"    … {type(e).__name__}, повтор через {wait}s")
                time.sleep(wait)
                continue
            print(f"  ✖ {item['id']}: {type(e).__name__}")
            return False

    if data is None:
        return False

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                dest = PENDING / f"{item['id']}_bg.png"
                dest.write_bytes(base64.b64decode(blob["data"]))
                print(f"  ✔ {item['id']} [{item['kind']}] "
                      f"({dest.stat().st_size // 1024} KB)")
                return True

    print(f"  ✖ {item['id']}: изображение не вернулось")
    return False


def main():
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    defaults = plan["defaults"]
    items = plan["stories"]

    args = sys.argv[1:]
    if "--week" in args:
        week = int(args[args.index("--week") + 1])
        items = [i for i in items if i.get("week") == week]
        print(f"тиждень {week}")
    else:
        ids = {a for a in args if not a.startswith("--")}
        if ids:
            items = [i for i in items if i["id"] in ids]

    if "--force" not in args:
        items = [i for i in items
                 if not (PENDING / f"{i['id']}_bg.png").exists()]

    if not items:
        print("нечего генерировать (всё есть, или --force)")
        return

    PENDING.mkdir(parents=True, exist_ok=True)
    tok = token()
    print(f"модель {IMAGE_MODEL} @ {GCP_LOCATION}, {IMAGE_SIZE}, кадров {len(items)}\n")

    ok = 0
    for n, item in enumerate(items):
        ok += generate(item, defaults, tok)
        if n < len(items) - 1:
            time.sleep(PAUSE)
    print(f"\nготово: {ok} из {len(items)}")


if __name__ == "__main__":
    main()
