# -*- coding: utf-8 -*-
"""Кадры от момента, а не от макета.

Прошлые промпты описывали вёрстку — «swiss poster», «editorial spread».
Модель отрабатывала макет, и все стили выходили на одно лицо. Здесь
описывается происходящее: что делают руки, откуда свет, что лежит рядом
неаккуратно. Ощущение — «снято на телефон», а не рекламная съёмка.

    python shots.py --list
    python shots.py --shot ritual-chaga
    python shots.py --all --tries 2

Текста ровно столько, сколько нужно слайду: none / short / long.
Кадры с текстом прогоняются через вычитку, кадры без текста — через
проверку, что модель не подрисовала надписей от себя.
"""
import sys
import time

import yaml

import fullgen as F
import generate as gen
import verify_frame as V
from config import CONTENT_DIR, OUT_DIR

SHOTS = CONTENT_DIR / "shots.yaml"
OUTDIR = OUT_DIR / "shots"

# Модель текст НЕ пишет. Проверено: на длинной фразе она сделала опечатку
# («хвиляину»), а вычитчик её не поймал — читающая модель молча исправляет
# ошибки при распознавании. Значит орфографию в нарисованном тексте
# проверить нечем, и надпись кладёт PIL.
NO_TEXT = """There must be NO text in the image at all — no letters, no numbers,
no words, no labels, no signage, no writing on jars, packets or anything else.
Not a single character anywhere."""

# Под надпись нужно оставить спокойное место, иначе текст ляжет на кашу
ROOM = {
    "none": "",
    "short": ("\nKeep the upper third of the frame calm and uncluttered — "
              "one line of text will be placed over it afterwards."),
    "long": ("\nKeep the upper 40 percent of the frame calm and uncluttered — "
             "several lines of text will be placed over it afterwards."),
}

TEMPLATE = """{base}

WHAT IS HAPPENING: {moment}

CAMERA: {camera}
LIGHT: {light}
IMPERFECTIONS THAT MAKE IT REAL: {imperfect}

Hands in frame are good. NEVER show a face.

{text_rule}

MUST NOT CONTAIN: {negative}
"""


def build(shot: dict, cfg: dict) -> str:
    # У мальованих кадрів своя база: телефонна прямо каже «фото», і з
    # ботанічним нарисом це суперечить одне одному
    default = (cfg.get("base_illustration") if shot.get("hero") == "illustration"
               else cfg["base"])
    base = shot.get("style_override", default).strip()
    rule = NO_TEXT + ROOM[shot.get("text", "none")]
    return TEMPLATE.format(
        base=base, moment=" ".join(shot["moment"].split()),
        camera=shot["camera"], light=shot["light"],
        imperfect=" ".join(shot["imperfect"].split()),
        text_rule=rule, negative=" ".join(cfg["negative"].split()))


def expected(shot: dict) -> list:
    """Ожидаемых строк нет: на кадре не должно быть НИ ОДНОЙ надписи."""
    return []


def make(shot: dict, cfg: dict, tok: str, tries=2) -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    key = shot["key"]
    dest = OUTDIR / f"{key}.png"
    prompt = build(shot, cfg)
    want = expected(shot)
    last = None

    for n in range(1, tries + 1):
        if not F.draw_raw(prompt, tok, dest):
            print(f"  ✖ {key}: не намалювалось (спроба {n})")
            continue
        res = V.check(dest, want, tok)
        # У кадра без текста своя проверка: там брак — это ЛЮБАЯ надпись,
        # которую модель добавила от себя
        if not want:
            seen = res.get("seen", {})
            lines = [l for l in seen.get("text_lines", []) if l.strip()]
            res = {"ok": not lines,
                   "why": [] if not lines else
                          [f"домальований текст: {' | '.join(lines)[:70]}"],
                   "seen": seen}
        last = res
        if res["ok"]:
            print(f"  ✔ {key:20} чисто з {n}-ї спроби")
            return {"key": key, "ok": True, "tries": n}
        print(f"  ~ {key:20} спроба {n}: " + "; ".join(res["why"])[:100])
        if n < tries:
            time.sleep(6)
    print(f"  ✖ {key:20} брак після {tries} спроб")
    return {"key": key, "ok": False, "tries": tries,
            "why": (last or {}).get("why", [])}


def main() -> int:
    cfg = yaml.safe_load(SHOTS.read_text(encoding="utf-8"))
    shots = {s["key"]: s for s in cfg["shots"]}

    if "--list" in sys.argv:
        for k, s in shots.items():
            print(f"  {k:20} [{s.get('text','none'):5}] {s['about']}")
        return 0

    want = []
    if "--shot" in sys.argv:
        want = [sys.argv[sys.argv.index("--shot") + 1]]
    elif "--all" in sys.argv:
        want = list(shots)
    if not want:
        print("вкажи --shot <ключ> або --all; список: --list")
        return 1

    tries = 2
    if "--tries" in sys.argv:
        tries = int(sys.argv[sys.argv.index("--tries") + 1])

    if "--print" in sys.argv:
        print(build(shots[want[0]], cfg))
        return 0

    tok = gen.token()
    print(f"кадрів {len(want)}, спроб до {tries}\n")
    rows = []
    for n, k in enumerate(want):
        rows.append(make(shots[k], cfg, tok, tries))
        if n < len(want) - 1:
            time.sleep(6)

    ok = sum(r["ok"] for r in rows)
    print(f"\nчистих: {ok} з {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
