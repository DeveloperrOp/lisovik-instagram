# -*- coding: utf-8 -*-
"""Перезаливка перемальованих кадрів у сховище.

Кадр, який уже стоїть у черзі, лежить у GCS під своїм id. Якщо текст на
ньому переписали й перемалювали, у черзі лишається СТАРА картинка:
маніфест зберігає посилання, а не файл.

Ім'я обʼєкта в сховищі те саме, тому перезаливка не міняє посилання —
досить надіслати новий файл під тим самим ім'ям.

    python reupload.py day3_osnova day3_spokij
    python reupload.py --all
"""
import shutil
import sys
from pathlib import Path

import yaml

import manifest as mf
from config import CONTENT_DIR, OUT_DIR

PENDING = OUT_DIR / "pending"


def main() -> int:
    sets = [a for a in sys.argv[1:] if not a.startswith("--")]
    m = mf.load()
    tok = mf.token()
    # id у маніфесті: «0906-osnova-dawn». Набір і слот беремо звідти й
    # шукаємо свіжий файл у теці дня.
    keys = {}
    for path in sorted(CONTENT_DIR.glob("day*.yaml")):
        if sets and path.stem not in sets:
            continue
        items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        stem = path.stem.split("_", 1)[-1]
        for t in items:
            keys[(stem, t["slot"])] = OUT_DIR / path.stem / f"{t['key']}.jpg"
        keys[(stem, "night")] = (OUT_DIR / path.stem /
                                 f"{path.stem}-offer.jpg")

    PENDING.mkdir(parents=True, exist_ok=True)
    done = 0
    for i in m["items"]:
        if i["status"] not in ("pending", "approved"):
            continue
        bits = i["id"].split("-")
        src = keys.get((bits[1], bits[-1])) if len(bits) > 2 else None
        if not src or not src.exists():
            continue
        dst = PENDING / f"{i['id']}.jpg"
        # Однакові файли не ганяємо в мережу заново.
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue
        shutil.copy2(src, dst)
        i["media_url"] = mf.upload_media(dst, tok)
        print(f"  ↑ {i['id']}")
        done += 1

    mf.save(m, tok)
    print(f"\nперезалито кадрів: {done}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
