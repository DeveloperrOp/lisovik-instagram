# -*- coding: utf-8 -*-
"""Примеры всех семи типов сторис — чтобы утвердить внешний вид до потока.

    python make_examples.py

Товарный кадр генерится с референсом реального фото: банка, этикетка и логотип
остаются как есть. Остальные типы — сцена от модели плюс вёрстка PIL.
"""
import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image

import layouts
from config import (CONTENT_DIR, GCP_LOCATION, GCP_PROJECT, IMAGE_MODEL,
                    IMAGE_SIZE, OUT_DIR)

REAL = Path(__file__).resolve().parents[1] / "samples" / "real"
DEST = OUT_DIR / "examples"

EXAMPLES = [
    {
        "kind": "product",
        "id": "ex-1-product",
        "photo": "LIS-469809.jpg",
        "headline": "ФОКУС З РАНКУ",
        "subline": "Мелений 50 г · веган",
        "scene": "soft morning forest clearing, moss and fern, warm low sun, "
                 "shallow depth of field",
    },
    {
        "kind": "fact",
        "id": "ex-2-fact",
        "headline": "ЇЖОВИК РОСТЕ НА СТАРИХ ДЕРЕВАХ",
        "subline": "І справді схожий на білу бороду",
        "scene": "moody forest interior, old trunk with deep bark texture, "
                 "misty depth, no objects in the centre of the frame",
    },
    {
        "kind": "howto",
        "id": "ex-3-howto",
        "headline": "ЯК ЗАВАРИТИ ЧАГУ",
        "steps": ["Залий окропом 80 °C", "Настоюй 15 хвилин", "Проціди і пий теплим"],
        "scene": "dark wooden table with a glass teapot far in the background, "
                 "warm side light, plenty of empty dark space",
    },
    {
        "kind": "compare",
        "id": "ex-4-compare",
        "headline": "ПОРОШОК ЧИ КАПСУЛИ",
        "options": [
            {"title": "ПОРОШОК", "text": "У каші, смузі та супі. Дешевше за грам"},
            {"title": "КАПСУЛИ", "text": "Без смаку, зручно брати з собою"},
        ],
        "scene": "very dark blurred forest background, deep green tones, "
                 "even texture, no objects, no focal point",
    },
    {
        "kind": "review",
        "id": "ex-5-review",
        "quote": "Замовляю втретє. Смак трав'яний, п'ю зранку замість звичного напою",
        "author": "Оксана, Львів",
        "scene": "soft dark green gradient with faint fern silhouettes at the "
                 "edges, empty centre, calm and quiet",
    },
    {
        "kind": "ask",
        "id": "ex-6-ask",
        "headline": "ЩО ОБРАТИ НОВАЧКУ?",
        "subline": "Питай — відповім особисто",
        "scene": "quiet forest path at blue hour, low mist, soft light, "
                 "clean empty space in the middle of the frame",
    },
    {
        "kind": "mood",
        "id": "ex-7-mood",
        "headline": "СУБОТА У ЛІСІ",
        "subline": "Тиша, якої бракує",
        "scene": "wide forest clearing with tall ferns, golden hour rays "
                 "through pine trunks, peaceful and cinematic",
    },
]

PRODUCT_PROMPT = """Vertical 9:16 Instagram Story for a Ukrainian wellness brand.

The attached image is MY REAL PRODUCT. Keep this exact jar: identical shape,
identical label artwork, identical logo, identical Ukrainian wording.
Do not redesign it, do not invent packaging, do not change letters on the label.

Place it standing naturally in this scene: {scene}
The product owns the lower half. Upper third stays clean for text.

Render exactly these two Ukrainian lines in the upper third, bold clean
sans-serif, white with soft shadow:
Line 1: {headline}
Line 2: {subline}

Copy characters literally. Do not transliterate, do not translate,
do not duplicate lines. Apart from the product label, no other text.

MUST NOT CONTAIN: no red-and-white spotted mushrooms, no Amanita muscaria,
no people, no hands, no pills, no dosage numbers, no other brands.
"""

SCENE_PROMPT = """Vertical 9:16 background plate for an Instagram Story.

Scene: {scene}

This is a BACKGROUND ONLY. Large text will be placed on top of it later,
so keep the composition calm and uncluttered, without a strong focal point
in the middle.

Render NO TEXT AT ALL anywhere in the image.

MUST NOT CONTAIN: no text, no letters, no numbers, no logos, no packaging,
no red-and-white spotted mushrooms, no Amanita muscaria, no people,
no hands, no pills.
"""


def token() -> str:
    return subprocess.run("gcloud auth print-access-token", shell=True,
                          capture_output=True, text=True, check=True).stdout.strip()


def call_model(parts: list, tok: str):
    host = ("aiplatform.googleapis.com" if GCP_LOCATION == "global"
            else f"{GCP_LOCATION}-aiplatform.googleapis.com")
    url = (f"https://{host}/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
           f"/publishers/google/models/{IMAGE_MODEL}:generateContent")
    body = {
        "contents": [{"role": "user", "parts": parts}],
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
                print(f"    … HTTP {e.code}, повтор через {wait}s")
                time.sleep(wait)
                continue
            print(f"    ✖ HTTP {e.code}: {e.read()[:150]}")
            return None
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                return Image.open(BytesIO(base64.b64decode(blob["data"])))
    return None


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    defaults = yaml.safe_load((CONTENT_DIR / "defaults.yaml").read_text(encoding="utf-8"))
    cta, disc = defaults["cta"], defaults["disclaimer"]
    tok = token()

    for n, ex in enumerate(EXAMPLES):
        print(f"  {ex['id']} ({ex['kind']})")
        if ex["kind"] == "product":
            photo = REAL / ex["photo"]
            parts = [
                {"inlineData": {"mimeType": "image/jpeg",
                                "data": base64.b64encode(photo.read_bytes()).decode()}},
                {"text": PRODUCT_PROMPT.format(**ex)},
            ]
        else:
            parts = [{"text": SCENE_PROMPT.format(scene=ex["scene"])}]

        # Фон кэшируем: перевёрстка не должна стоить денег
        cache = DEST / "_bg" / f"{ex['id']}.png"
        cache.parent.mkdir(parents=True, exist_ok=True)
        if cache.exists():
            bg = Image.open(cache)
            print("    фон из кэша")
        else:
            bg = call_model(parts, tok)
            if bg is None:
                print("    пропускаю")
                continue
            bg.save(cache)

        out = layouts.render(ex["kind"], bg, ex, cta, disc)
        dest = DEST / f"{ex['id']}.jpg"
        out.save(dest, "JPEG", quality=92, optimize=True)
        print(f"    ✔ {dest.name} ({dest.stat().st_size // 1024} KB)")

        if n < len(EXAMPLES) - 1:
            time.sleep(10)


if __name__ == "__main__":
    main()
