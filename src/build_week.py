# -*- coding: utf-8 -*-
"""Сборка недели: фон под каждый кадр, вычитка, текст поверх.

Один день — один продукт, но визуальный язык внутри дня меняется, иначе
четыре кадра подряд читаются как один. Языки берутся из looks.yaml,
тексты — из final_week.yaml, надпись рисует PIL.

    python build_week.py --day mon
    python build_week.py --all
    python build_week.py --compose        # только собрать, не рисовать

Фон рисуется без единой буквы и проходит вычитку: модель любит
подрисовать чужой никнейм или интерфейс. Текст кладётся сверху.
"""
import sys
import time

import yaml
from PIL import Image

import fullgen as F
import generate as gen
import looks as L
import overlays as O
import verify_frame as V
from config import CONTENT_DIR, OUT_DIR

WEEK = CONTENT_DIR / "final_week.yaml"
OUTDIR = OUT_DIR / "week"

# Что стоит в кадре в каждый день. Описание предметное: модель рисует
# то, что названо, а не «функциональный гриб вообще».
SUBJECT = {
    "mon": ("lion's mane mushroom: a white cascading cluster of soft hanging "
            "spines, and pale cream ground powder made from it"),
    "tue": ("birch chaga: a hard cracked black chunk with a rust-orange "
            "interior, and the deep amber infusion brewed from it"),
    "wed": ("cordyceps militaris: slender bright orange club-shaped fruiting "
            "bodies, and orange powder ground from them"),
    "thu": ("ashwagandha: dried pale woody roots and the fine beige powder "
            "ground from them, with a cup of warm milk"),
    "fri": ("reishi mushroom: a hard glossy kidney-shaped bracket with "
            "concentric rings, dark red-brown, and a dark bitter decoction"),
    "sat": ("spirulina and chlorella: two deep green powders, one blue-green "
            "and one grass-green, and a glass of green drink"),
    "sun": ("a row of plain glass jars of different powders on a clean shelf, "
            "a measuring spoon and a paper calendar page"),
}

# Порядок языков внутри дня: тёмный, светлый, цветной, природный.
# Соседние кадры не должны попадать в один регистр.
ROTATION = ["studio-dark", "knolling", "levitation", "nature-light",
            "macro-texture", "cinematic-dark", "splash"]


def look_for(day_index: int, slot: int) -> str:
    """Свой язык каждому кадру, со сдвигом по дням — иначе все понедельники
    и все вторники будут выглядеть одинаково."""
    return ROTATION[(day_index * 2 + slot) % len(ROTATION)]


def draw_bg(key: str, subject: str, look_key: str, cfg: dict, tok: str,
            tries=2) -> bool:
    dest = OUTDIR / f"{key}.png"
    if dest.exists():
        print(f"  · {key}: підкладка вже є", flush=True)
        return True
    looks = {x["key"]: x for x in cfg["looks"]}
    prompt = L.TEMPLATE.format(
        subject=subject,
        look=" ".join(looks[look_key]["prompt"].split()),
        # negative разделён на два поля (см. looks.yaml): здесь все языки
        # предметные, поэтому «людей нет» добавляется всегда.
        negative=" ".join((cfg["negative"] + " "
                           + cfg.get("negative_still", "")).split()))
    for n in range(1, tries + 1):
        if not F.draw_raw(prompt, tok, dest):
            continue
        seen = V.check(dest, [], tok).get("seen", {})
        lines = [x for x in seen.get("text_lines", []) if x.strip()]
        if not lines:
            print(f"  ✔ {key:26} {look_key:14} з {n}-ї спроби", flush=True)
            return True
        print(f"  ~ {key}: домальований текст {' | '.join(lines)[:44]}",
              flush=True)
        time.sleep(5)
    print(f"  ✖ {key}: брак після {tries} спроб", flush=True)
    return False


def compose(items: list) -> int:
    ok = 0
    for t in items:
        bg = OUTDIR / f"{t['key']}.png"
        if not bg.exists():
            print(f"  ✖ {t['key']}: немає підкладки")
            continue
        out = O.render(Image.open(bg).convert("RGBA"), O.from_thought(t))
        out.convert("RGB").save(OUTDIR / f"{t['key']}.jpg", "JPEG", quality=91)
        ok += 1
    print(f"\nзібрано кадрів: {ok} із {len(items)}")
    return ok


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    week = yaml.safe_load(WEEK.read_text(encoding="utf-8"))["thoughts"]
    cfg = yaml.safe_load((CONTENT_DIR / "looks.yaml").read_text(encoding="utf-8"))

    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    want = days
    if "--day" in sys.argv:
        want = [sys.argv[sys.argv.index("--day") + 1]]
    items = [t for t in week if t["day"] in want]

    if "--compose" in sys.argv:
        return 0 if compose(items) else 1

    tok = gen.token()
    print(f"кадрів {len(items)}\n", flush=True)
    for t in items:
        di, slot = days.index(t["day"]), [x["key"] for x in week
                                          if x["day"] == t["day"]].index(t["key"])
        draw_bg(t["key"], SUBJECT[t["day"]], look_for(di, slot), cfg, tok)
        time.sleep(4)
    compose(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
