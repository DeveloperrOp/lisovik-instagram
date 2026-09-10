# -*- coding: utf-8 -*-
"""Карусель у стрічку: кілька кадрів 4:5 про один товар.

Пост «Товар тижня» — одна картинка, і на ній не розкажеш ні складу, ні
схеми прийому. Для курсу цього мало: людина гортає й читає по кроку на
кадр. Ярик 10.09: «надо сделать фото каруселью, на подобие тех что уже
есть про другие продукты».

Кадри беруться з content/post_*.yaml тим самим форматом, що й сторіс,
тому працюють ті самі перевірки: check_thought для тексту, вичитка
етикеток у build_day, наші банки за референсом.

    python check_thought.py ../content/post_osnova.yaml   # спершу текст
    python post_carousel.py ../content/post_osnova.yaml   # намалювати
    python post_carousel.py ../content/post_osnova.yaml --compose

Різниця зі сторіс одна — пропорція 4:5 замість 9:16.
"""
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

import build_day as B
import generate as gen
import overlays as O
from config import CONTENT_DIR, OUT_DIR

W, H = 1080, 1350
NL = chr(10)
BREAK = NL + NL


def caption_text(raw: str) -> str:
    """Підпис із YAML → текст для стрічки.

    Блок «|» у YAML тримає жорсткі переноси — так зручно читати у файлі.
    В інстаграмі такий текст виглядає рваним, тому рядки всередині абзацу
    склеюємо назад в один. Порожній рядок лишається межею абзацу, а
    пункти списку живуть окремими рядками, як і задумано.
    """
    out = []
    for para in (raw or "").strip().split(BREAK):
        lines = [x.strip() for x in para.split(NL) if x.strip()]
        if not lines:
            continue
        out.append(NL.join(lines) if any(x[:1] in "-•" for x in lines)
                   else " ".join(lines))
    return BREAK.join(out)


def sheet(items: list, outdir: Path) -> None:
    """Лист усієї каруселі: пост дивляться підряд, а не по кадру."""
    shots = [Image.open(outdir / f"{t['key']}.jpg")
             for t in items if (outdir / f"{t['key']}.jpg").exists()]
    if not shots:
        return
    tw = 300
    th = [i.resize((tw, int(tw * i.height / i.width))) for i in shots]
    page = Image.new("RGB", (len(th) * (tw + 10) + 10, th[0].height + 34),
                     (18, 18, 20))
    d = ImageDraw.Draw(page)
    for i, im in enumerate(th):
        page.paste(im, (10 + i * (tw + 10), 26))
        d.text((14 + i * (tw + 10), 8), f"{i + 1}", fill=(240, 200, 60))
    page.save(outdir / "_carousel.jpg", "JPEG", quality=92)
    print(f"лист каруселі: {outdir / '_carousel.jpg'}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0] if args else CONTENT_DIR / "post_osnova.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    items = data["thoughts"]
    cfg = yaml.safe_load((CONTENT_DIR / "looks.yaml").read_text(
        encoding="utf-8"))
    looks = {x["key"]: x for x in cfg["looks"]}

    outdir = OUT_DIR / path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    if "--compose" not in sys.argv:
        tok = gen.token()
        print(f"кадрів {len(items)}  ({W}×{H}, 4:5)\n", flush=True)
        for t in items:
            B.draw_bg(t, cfg, looks, outdir, tok, aspect="4:5")

    ok = 0
    for t in items:
        bg = outdir / f"{t['key']}.png"
        if not bg.exists():
            print(f"  ✖ {t['key']}: немає підкладки")
            continue
        img = Image.open(bg).convert("RGBA").resize((W, H))
        O.render(img, O.from_thought(t)).convert("RGB").save(
            outdir / f"{t['key']}.jpg", "JPEG", quality=92)
        ok += 1
    print(f"\nзібрано кадрів: {ok} із {len(items)}")
    cap = caption_text(data.get("caption", ""))
    if cap:
        (outdir / "caption.txt").write_text(cap, encoding="utf-8")
        print(f"підпис: {len(cap)} символів")
    sheet(items, outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
