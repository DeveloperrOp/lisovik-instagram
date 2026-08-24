# -*- coding: utf-8 -*-
"""Вычитка готового кадра: что на нём НА САМОМ ДЕЛЕ написано.

Когда текст рисует модель, а не PIL, линтер слепнет: он проверяет YAML,
а в пикселях не видит ничего. А модель ошибается ровно так, как заметно
только глазом — подрисовывает латинскую закорючку, режет заголовок краем
кадра, дублирует букву.

Поэтому кадр вычитывается вторым проходом: отдаём картинку модели и
спрашиваем, какой текст она видит. Дальше сверяем с тем, что заказывали.

    python verify_frame.py out/fullgen/collage.png "ЗАГОЛОВОК" "підпис"

Возвращает вердикт: совпал ли текст и нет ли лишних надписей.
"""
import base64
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

from config import GCP_LOCATION, GCP_PROJECT, IMAGE_MODEL

# Текстовых моделей в проекте нет (gemini-3.1-flash и gemini-3-pro отдают
# 404), но image-модель принимает картинку на вход и умеет отвечать текстом
READER = IMAGE_MODEL

ASK = """Ти вичитувач макета. Подивись на зображення і опиши ЛИШЕ факти.

Випиши ВЕСЬ текст, який бачиш на зображенні, рядок за рядком, точно як
написано. Включно з дрібними написами, підписами, позначками, підписами
від руки, будь-якими літерами в кутах і на полях. Нічого не пропускай і
нічого не додавай від себе.

Окремо назви:
1. Чи є на зображенні хоч один напис ЛАТИНКОЮ (латинськими літерами).
2. Чи обрізаний якийсь текст краєм кадру.
3. Чи повторюється якийсь напис двічі.

Відповідай СТРОГО у форматі JSON, без пояснень навколо:
{"text_lines": ["рядок", "рядок"], "has_latin": true/false,
 "latin_found": "що саме", "cropped": true/false, "duplicated": true/false,
 "notes": "коротко"}"""


def token() -> str:
    return subprocess.run("gcloud auth print-access-token", shell=True,
                          capture_output=True, text=True, check=True).stdout.strip()


def as_seen(path: Path) -> str:
    """Кадр в том размере, в каком его увидит зритель.

    Отдавать исходные 1536x2752 PNG на 5-7 МБ незачем: проверяем ровно то,
    что уйдёт в ленту, и payload меньше в разы.
    """
    img = Image.open(path).convert("RGB")
    if img.width != 1080:
        img = img.resize((1080, round(1080 * img.height / img.width)),
                         Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()


def read_frame(path: Path, tok: str) -> dict:
    host = ("aiplatform.googleapis.com" if GCP_LOCATION == "global"
            else f"{GCP_LOCATION}-aiplatform.googleapis.com")
    url = (f"https://{host}/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}"
           f"/publishers/google/models/{READER}:generateContent")
    body = {
        "contents": [{"role": "user", "parts": [
            {"inlineData": {"mimeType": "image/jpeg", "data": as_seen(path)}},
            {"text": ASK},
        ]}],
        # responseModalities: ["TEXT"] эта модель отвергает с 400 — она
        # генеративная по картинкам, и текст-онли ей задать нельзя.
        # Просто берём из ответа текстовые части, картинку игнорируем.
    }
    data = None
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
                time.sleep(20 * attempt)
                continue
            raise RuntimeError(f"вичитувач: HTTP {e.code} "
                               f"{e.read().decode('utf-8', 'replace')[:160]}") from None
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            # Обрыв связи не должен ронять всю пачку: в генераторе такая
            # защита есть, а здесь её сначала не было — и пачка из десяти
            # стилей легла на середине из-за одного отвалившегося сокета
            if attempt < 5:
                time.sleep(20 * attempt)
                continue
            raise RuntimeError(f"вичитувач: {type(e).__name__} {str(e)[:120]}") from None
    if data is None:
        raise RuntimeError("вичитувач не відповів")

    out = ""
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            out += part.get("text", "")
    out = out.strip()
    if out.startswith("```"):
        out = out.split("```")[1]
        out = out[4:] if out.lower().startswith("json") else out
    try:
        return json.loads(out.strip())
    except json.JSONDecodeError:
        return {"raw": out[:400], "parse_error": True}


def norm(s: str) -> str:
    """Для сравнения: без регистра, без пунктуации, без лишних пробелов."""
    keep = "".join(c if c.isalnum() or c.isspace() else " " for c in s.lower())
    return " ".join(keep.split())


def check(path: Path, expected: list, tok=None) -> dict:
    tok = tok or token()
    # Изредка модель отвечает не JSON-ом. Это сбой вычитчика, а не брак
    # кадра: если засчитать его браком, нормальный кадр уйдёт на перерисовку
    seen = read_frame(path, tok)
    if seen.get("parse_error"):
        time.sleep(4)
        seen = read_frame(path, tok)
    if seen.get("parse_error"):
        return {"ok": False, "why": ["вичитувач не повернув JSON двічі"],
                "seen": seen}

    blob = norm(" ".join(seen.get("text_lines", [])))
    why = []
    for want in expected:
        if norm(want) not in blob:
            why.append(f"немає рядка: «{want[:46]}»")
    if seen.get("has_latin"):
        why.append(f"латинка в кадрі: {seen.get('latin_found', '')[:40]}")
    if seen.get("cropped"):
        why.append("текст обрізаний краєм кадру")
    if seen.get("duplicated"):
        why.append("напис повторюється двічі")
    return {"ok": not why, "why": why, "seen": seen}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    expected = sys.argv[2:]
    r = check(path, expected)
    print(f"{path.name}: " + ("ЧИСТО ✓" if r["ok"] else "БРАК ✖"))
    for w in r["why"]:
        print("   ", w)
    print("   побачений текст:", " | ".join(r["seen"].get("text_lines", []))[:200])
    return 0 if r["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
