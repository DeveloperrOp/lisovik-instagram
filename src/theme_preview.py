# -*- coding: utf-8 -*-
"""Образцы вайбов: один и тот же кадр во всех темах.

Нужен до того, как гнать целую неделю: тема меняет свет и палитру, и
понять, работает ли она, можно только глазами. Гнать 28 кадров ради
этого — расточительство.

    python theme_preview.py            # все темы
    python theme_preview.py --kind product
    python theme_preview.py rankova-kuhnya zemlya-i-hlyna

Кладёт в out/themes/: по кадру на тему плюс общий лист для сравнения.
"""
import sys
import time

import yaml
from PIL import Image

import generate as gen
import layouts
import theme
from config import CONTENT_DIR, OUT_DIR

OUTDIR = OUT_DIR / "themes"

# Нейтральная сцена: пусть вайб задаёт стиль темы, а не текст сцены,
# иначе сравниваем не темы, а разные описания
SCENE = "quiet still-life corner, empty calm centre, nothing sharp in focus"

SAMPLE = {
    "useful": {
        "kind": "useful", "id": "sample",
        "headline": "ЧАГА ЛЮБИТЬ ТЕПЛО, А НЕ ОКРІП",
        "body": "Окріп руйнує частину сполук, заради яких чагу й заварюють. "
                "Тому її не кидають у щойно закипілу воду.",
        "tip": "Дай воді постояти хвилину-дві після закипання",
    },
    "howto": {
        "kind": "howto", "id": "sample",
        "headline": "ЯК ЗАВАРИТИ ЧАГУ",
        "steps": ["Залий окропом 80 °C", "Настоюй 15 хвилин", "Проціди і пий теплим"],
    },
    "compare": {
        "kind": "compare", "id": "sample",
        "headline": "ПОРОШОК ЧИ КАПСУЛИ",
        "options": [
            {"title": "ПОРОШОК", "points": ["Дешевше за порцію", "Легко в кашу",
                                            "Сам регулюєш обʼєм", "Смак відчувається"]},
            {"title": "КАПСУЛИ", "points": ["Смаку немає", "Зручно з собою",
                                            "Нічого не відмірювати", "Дорожче за грам"]},
        ],
    },
}


def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main() -> int:
    kind = arg("--kind", "useful")
    if kind not in SAMPLE:
        print(f"немає зразка «{kind}»; є: {', '.join(SAMPLE)}")
        return 1

    # Значение флага не должно попасть в список тем: «--kind compare»
    # превращало compare в имя темы, и не совпадало ничего
    argv, wanted, skip = sys.argv[1:], [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == "--kind":
            skip = True
        elif not a.startswith("--"):
            wanted.append(a)
    themes = [t for t in theme.all_themes()
              if not wanted or t["key"] in wanted]
    if not themes:
        print("жодна тема не збіглась")
        return 1

    defaults = yaml.safe_load(
        (CONTENT_DIR / "defaults.yaml").read_text(encoding="utf-8"))
    OUTDIR.mkdir(parents=True, exist_ok=True)

    tok = gen.token()
    print(f"зразок «{kind}», тем: {len(themes)}\n")

    shots = []
    for n, t in enumerate(themes):
        bg_path = OUTDIR / f"{t['key']}_bg.png"
        if not bg_path.exists() or "--force" in sys.argv:
            # generate пишет в out/pending/{id}_bg.png — подсовываем id темы
            item = {"id": f"theme-{t['key']}", "kind": "mood", "scene": SCENE,
                    "week": None}
            fake = dict(defaults)
            fake["style"] = t["style"]
            if not gen.generate(item, fake, tok):
                print(f"  ✖ {t['name']}: підкладка не намалювалась")
                continue
            (gen.PENDING / f"theme-{t['key']}_bg.png").replace(bg_path)
            if n < len(themes) - 1:
                time.sleep(gen.PAUSE)

        theme.apply(t)
        img = layouts.render(kind, Image.open(bg_path), dict(SAMPLE[kind]),
                             defaults["cta"], defaults["disclaimer"])
        dest = OUTDIR / f"{t['key']}.jpg"
        img.save(dest, "JPEG", quality=92)
        print(f"  ✔ {t['name']:16} → {dest.name}")
        shots.append((t["name"], img))

    if len(shots) > 1:
        tw = 330
        th = [(nm, im.resize((tw, int(tw * im.height / im.width))))
              for nm, im in shots]
        sheet = Image.new("RGB", (tw * len(th) + 10 * (len(th) - 1),
                                  th[0][1].height), (22, 22, 22))
        for i, (_, im) in enumerate(th):
            sheet.paste(im, (i * (tw + 10), 0))
        sheet.save(OUTDIR / f"_sheet_{kind}.jpg", "JPEG", quality=86)
        print(f"\nлист порівняння → {OUTDIR / f'_sheet_{kind}.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
