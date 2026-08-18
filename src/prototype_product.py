# -*- coding: utf-8 -*-
"""Прототип продуктовой сторис: РЕАЛЬНОЕ фото товара, а не выдуманная банка.

Фото карточки передаётся модели референсом, и она обязана сохранить банку,
этикетку и логотип как есть — только переносит в вертикальную сцену.

Смысловая структура взята с существующих карточек Лісовика:
    заголовок = польза  →  «ФОКУС З РАНКУ»
    строка характеристик = конкретика  →  «МЕЛЕНИЙ 50 Г · 25 ДНІВ · ВЕГАН»

    python prototype_product.py
"""
import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from config import (GCP_LOCATION, GCP_PROJECT, IMAGE_MODEL, IMAGE_SIZE,
                    OUT_DIR)

REAL = Path(__file__).resolve().parents[1] / "samples" / "real"
DEST = OUT_DIR / "prototype"

# заголовок — обіцянка користі, підзаголовок — суха конкретика
CASES = [
    {
        "id": "proto-yizhovyk",
        "photo": "LIS-469809.jpg",
        "headline": "ФОКУС З РАНКУ",
        "subline": "Мелений 50 г · веган",
        "scene": "soft morning forest clearing, moss and fern, warm low sun, "
                 "shallow depth of field",
    },
    {
        "id": "proto-chaha",
        "photo": "LIS-481438.jpg",
        "headline": "ЧАГА У ЧАЙ",
        "subline": "Ціла 50 г · без хімії",
        "scene": "white birch grove in cold morning light, frost on bark, "
                 "quiet winter forest",
    },
]

PROMPT = """Vertical 9:16 Instagram Story for a Ukrainian wellness brand.

The attached image is MY REAL PRODUCT. Keep this exact jar or package:
identical shape, identical label artwork, identical logo, identical Ukrainian
wording on the label. Do not redesign it, do not invent new packaging,
do not change any letters on the label.

Place the product in this scene, standing naturally on a surface:
{scene}

Composition: the product occupies the lower half and is clearly the hero.
The upper third stays clean and uncluttered for text.

Render exactly these two Ukrainian text lines in the upper third,
bold clean sans-serif, white with a soft shadow:
Line 1: {headline}
Line 2: {subline}

TEXT RULES:
- Copy characters literally, correct Ukrainian Cyrillic.
- Do not transliterate, do not translate, do not duplicate lines.
- Apart from the label on the product itself, no other text anywhere.

MUST NOT CONTAIN: no red-and-white spotted mushrooms, no Amanita muscaria,
no people, no hands, no pills, no dosage numbers, no other brands,
no invented packaging.
"""


def token() -> str:
    return subprocess.run("gcloud auth print-access-token", shell=True,
                          capture_output=True, text=True, check=True).stdout.strip()


def generate(case: dict, tok: str) -> bool:
    photo = REAL / case["photo"]
    if not photo.exists():
        print(f"  ✖ нет фото {photo.name}")
        return False

    host = ("aiplatform.googleapis.com" if GCP_LOCATION == "global"
            else f"{GCP_LOCATION}-aiplatform.googleapis.com")
    url = (f"https://{host}/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
           f"/publishers/google/models/{IMAGE_MODEL}:generateContent")

    body = {
        "contents": [{"role": "user", "parts": [
            {"inlineData": {"mimeType": "image/jpeg",
                            "data": base64.b64encode(photo.read_bytes()).decode()}},
            {"text": PROMPT.format(**case)},
        ]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "9:16", "imageSize": IMAGE_SIZE},
        },
    }

    for attempt in range(1, 6):
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {tok}",
                     "X-Goog-User-Project": GCP_PROJECT,
                     "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 5:
                wait = 25 * attempt
                print(f"  … {case['id']}: HTTP {e.code}, повтор через {wait}s")
                time.sleep(wait)
                continue
            print(f"  ✖ {case['id']}: HTTP {e.code} {e.read()[:160]}")
            return False

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                dest = DEST / f"{case['id']}.png"
                dest.write_bytes(base64.b64decode(blob["data"]))
                print(f"  ✔ {case['id']} → {dest.name}")
                return True
    print(f"  ✖ {case['id']}: изображение не вернулось")
    return False


if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    tok = token()
    print(f"прототип на реальных фото товара, модель {IMAGE_MODEL}\n")
    for n, c in enumerate(CASES):
        generate(c, tok)
        if n < len(CASES) - 1:
            time.sleep(10)
