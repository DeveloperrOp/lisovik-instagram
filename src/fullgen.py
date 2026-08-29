# -*- coding: utf-8 -*-
"""Кадр целиком рисует модель, вычитчик ловит брак, брак перерисовывается.

Раньше текст на сторис накладывал PIL: модель не держала украинский и
подрисовывала отсебятину. На 2K она пишет чисто — проверено, — но всё
ещё умеет подсунуть латинскую закорючку в угол или срезать заголовок
краем кадра. Такой брак не видит ни один линтер: он проверяет YAML, а
не пиксели.

Поэтому цикл здесь такой: нарисовать → вычитать готовое → не сошлось,
рисовать заново. Юридическую строку модель не пишет никогда, её ставит
PIL поверх.

    python fullgen.py --styles              # какие стили есть
    python fullgen.py --style editorial-serif
    python fullgen.py --all --tries 3
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.request

import yaml

import generate as gen
import verify_frame as V
from config import CONTENT_DIR, GCP_LOCATION, GCP_PROJECT, IMAGE_MODEL, IMAGE_SIZE, OUT_DIR

STYLES_FILE = CONTENT_DIR / "fullgen_styles.yaml"
OUTDIR = OUT_DIR / "fullgen"

PROMPT = """Vertical 9:16 Instagram Story — a FINISHED graphic design, not a photo.

Set this Ukrainian text as the typography of the design.
Headline, large and dominant:
    {head}
Supporting line, clearly smaller:
    {body}

Art direction: {style}

TEXT RULES — these matter more than beauty:
- Reproduce the Ukrainian letter for letter, exactly as written above.
- Do NOT transliterate into Latin. Do NOT add a Latin version anywhere.
- Do NOT write ANY word in Latin letters — no signatures, no handwritten
  marks, no small captions in the corners, no brand names. Not one.
- Do NOT repeat the headline twice anywhere in the frame.
- Do NOT invent extra words, labels, numbers, dates or ornamental lettering.
- Ukrainian letters Ґ Є І Ї must be drawn correctly, not replaced.

COMPOSITION RULES:
- Every letter of the headline must be FULLY inside the frame, with a clear
  margin. Nothing may touch or cross the edge of the image.
- Leave the bottom 14 percent empty and calm — a legal line goes there later.

MUST NOT CONTAIN: red-and-white spotted mushrooms, Amanita muscaria,
people, faces, hands, pills, blister packs, medical imagery,
real-world brands or logos of any company, lorem ipsum, watermarks.
"""


def endpoint() -> str:
    host = ("aiplatform.googleapis.com" if GCP_LOCATION == "global"
            else f"{GCP_LOCATION}-aiplatform.googleapis.com")
    return (f"https://{host}/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
            f"/publishers/google/models/{IMAGE_MODEL}:generateContent")


def draw(head: str, body: str, style: str, tok: str, dest) -> bool:
    return draw_raw(PROMPT.format(head=head, body=body, style=style), tok, dest)


def draw_raw(prompt: str, tok: str, dest, aspect="9:16") -> bool:
    """Рисует по готовому промпту. Нужен тем, кто собирает промпт сам.

    Токен обновляем сами при 401: gcloud выдаёт его примерно на час, а
    пачка из десятка кадров идёт дольше — иначе половина прогона летит
    по причине, к качеству отношения не имеющей.
    """
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect, "imageSize": IMAGE_SIZE},
        },
    }
    return _post(payload, tok, dest)


def _post(payload: dict, tok: str, dest) -> bool:
    for attempt in range(1, 6):
        req = urllib.request.Request(
            endpoint(), data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {tok}",
                     "X-Goog-User-Project": GCP_PROJECT,
                     "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=420) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code == 401 and attempt < 5:
                print("      токен протух, оновлюю", flush=True)
                tok = gen.token()
                continue
            if e.code in (429, 500, 503) and attempt < 5:
                time.sleep(20 * attempt)
                continue
            print(f"      HTTP {e.code}", flush=True)
            return False
        except (TimeoutError, urllib.error.URLError, OSError):
            if attempt < 5:
                time.sleep(20 * attempt)
                continue
            return False
    else:
        return False

    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                dest.write_bytes(base64.b64decode(blob["data"]))
                return True
    return False


def make(key: str, style: str, head: str, body: str, tok: str, tries=3) -> dict:
    """Рисуем, вычитываем, при браке рисуем заново."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    dest = OUTDIR / f"{key}.png"
    last = None
    for n in range(1, tries + 1):
        if not draw(head, body, style, tok, dest):
            print(f"  ✖ {key}: не намалювалось (спроба {n})")
            continue
        res = V.check(dest, [head, body], tok)
        last = res
        if res["ok"]:
            print(f"  ✔ {key}  чисто з {n}-ї спроби")
            return {"key": key, "ok": True, "tries": n, "path": dest}
        print(f"  ~ {key}  спроба {n}: " + "; ".join(res["why"])[:110])
        if n < tries:
            time.sleep(8)
    print(f"  ✖ {key}: брак після {tries} спроб")
    return {"key": key, "ok": False, "tries": tries, "path": dest,
            "why": (last or {}).get("why", [])}


def main() -> int:
    cfg = yaml.safe_load(STYLES_FILE.read_text(encoding="utf-8"))
    styles = cfg["styles"]

    if "--styles" in sys.argv:
        for k, v in styles.items():
            print(f"  {k:22} {v['about']}")
        return 0

    want = []
    if "--style" in sys.argv:
        want = [sys.argv[sys.argv.index("--style") + 1]]
    elif "--all" in sys.argv:
        want = list(styles)
    if not want:
        print("вкажи --style <ключ> або --all; список: --styles")
        return 1

    tries = 3
    if "--tries" in sys.argv:
        tries = int(sys.argv[sys.argv.index("--tries") + 1])

    head, body = cfg["sample"]["headline"], cfg["sample"]["body"]
    tok = gen.token()

    # Вычитать уже нарисованное, ничего не перерисовывая: после обрыва
    # связи посреди пачки статус кадров неизвестен, а рисовать заново —
    # выбрасывать готовое
    if "--verify-only" in sys.argv:
        ok = 0
        for k in want:
            dest = OUTDIR / f"{k}.png"
            if not dest.exists():
                print(f"  — {k}: немає файлу")
                continue
            r = V.check(dest, [head, body], tok)
            ok += r["ok"]
            print(f"  {'✔' if r['ok'] else '✖'} {k:20} "
                  + ("чисто" if r["ok"] else "; ".join(r["why"])[:96]))
        print(f"\nчистих: {ok} з {len(want)}")
        return 0

    print(f"стилів {len(want)}, спроб на кожен до {tries}\n")

    rows = []
    for n, k in enumerate(want):
        rows.append(make(k, styles[k]["prompt"], head, body, tok, tries))
        if n < len(want) - 1:
            time.sleep(8)

    ok = sum(r["ok"] for r in rows)
    print(f"\nчистих: {ok} з {len(rows)}")
    for r in rows:
        if not r["ok"]:
            print(f"  брак — {r['key']}: " + "; ".join(r.get("why", []))[:110])
    return 0


if __name__ == "__main__":
    sys.exit(main())


def draw_ref(prompt: str, ref_path, tok: str, dest,
             aspect="9:16") -> bool:
    """Рисует по промпту ПЛЮС фото-референс товара.

    Владелец: «банка на фото не моя», потом — «дай референс». Описать
    упаковку словами не выходит: я трижды промахнулся по форме, крышке и
    этикетке. Модель же держит пакет точно, когда он приложен картинкой —
    это уже проверено на товарных кадрах в generate.py.

    Фото товара идёт только как образец упаковки. В кадр оно не
    публикуется: наружу уходит сгенерированная сцена.
    """
    import base64
    from pathlib import Path
    # ref_path может быть одним файлом или списком: для кадра со стопкой
    # банок нужно показать модели все упаковки сразу, иначе она рисует
    # одну настоящую и четыре выдуманные рядом.
    refs = ref_path if isinstance(ref_path, (list, tuple)) else [ref_path]
    parts = [{"inlineData": {"mimeType": "image/jpeg",
                             "data": base64.b64encode(
                                 Path(r).read_bytes()).decode()}}
             for r in refs]
    payload = {
        "contents": [{"role": "user", "parts": parts + [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect, "imageSize": IMAGE_SIZE},
        },
    }
    return _post(payload, tok, dest)
