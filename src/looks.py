# -*- coding: utf-8 -*-
"""Забор визуальных языков: один предмет, четырнадцать разных миров.

Три подхода подряд забракованы, и общая беда была одна — я каждый раз
давал вариации одной эстетики вместо выбора. Здесь предмет фиксирован,
а меняется сам язык: от студийной предметки до микроскопии и ризографии.

    python looks.py --list
    python looks.py --look studio-dark
    python looks.py --all --tries 2

Рук нет нигде, текста нет нигде: и то и другое забраковано отдельно.
"""
import sys
import time

import yaml

import fullgen as F
import generate as gen
import verify_frame as V
from config import CONTENT_DIR, OUT_DIR

LOOKS = CONTENT_DIR / "looks.yaml"
OUTDIR = OUT_DIR / "looks"

TEMPLATE = """Vertical 9:16 image for an Instagram Story.

SUBJECT: {subject}

VISUAL LANGUAGE — this is what decides how the image looks: {look}

There must be NO text in the image at all: no letters, no numbers,
no labels, no signage. Not a single character anywhere.
No hands, no arms, no people, no body parts.

Leave the upper third calm — a line of text is placed over it later.

MUST NOT CONTAIN: {negative}
"""


def build(look: dict, cfg: dict) -> str:
    return TEMPLATE.format(
        subject=" ".join(cfg["subject"].split()),
        look=" ".join(look["prompt"].split()),
        negative=" ".join(cfg["negative"].split()))


def make(look: dict, cfg: dict, tok: str, tries=2) -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    key = look["key"]
    dest = OUTDIR / f"{key}.png"
    prompt = build(look, cfg)

    for n in range(1, tries + 1):
        if not F.draw_raw(prompt, tok, dest):
            print(f"  ✖ {key}: не намалювалось (спроба {n})", flush=True)
            continue
        res = V.check(dest, [], tok)
        lines = [l for l in res.get("seen", {}).get("text_lines", []) if l.strip()]
        if not lines:
            print(f"  ✔ {key:18} чисто з {n}-ї спроби", flush=True)
            return {"key": key, "ok": True}
        print(f"  ~ {key:18} спроба {n}: домальований текст "
              f"{' | '.join(lines)[:60]}", flush=True)
        if n < tries:
            time.sleep(6)
    print(f"  ✖ {key:18} брак після {tries} спроб", flush=True)
    return {"key": key, "ok": False}


def main() -> int:
    cfg = yaml.safe_load(LOOKS.read_text(encoding="utf-8"))
    looks = {l["key"]: l for l in cfg["looks"]}

    if "--list" in sys.argv:
        for k, l in looks.items():
            print(f"  {k:18} {l['about']}")
        return 0

    want = []
    if "--look" in sys.argv:
        want = [sys.argv[sys.argv.index("--look") + 1]]
    elif "--all" in sys.argv:
        want = list(looks)
    if not want:
        print("вкажи --look <ключ> або --all; список: --list")
        return 1

    if "--print" in sys.argv:
        print(build(looks[want[0]], cfg))
        return 0

    tries = 2
    if "--tries" in sys.argv:
        tries = int(sys.argv[sys.argv.index("--tries") + 1])

    tok = gen.token()
    print(f"мов {len(want)}, спроб до {tries}\n", flush=True)
    rows = []
    for n, k in enumerate(want):
        rows.append(make(looks[k], cfg, tok, tries))
        if n < len(want) - 1:
            time.sleep(6)
    print(f"\nчистих: {sum(r['ok'] for r in rows)} з {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
