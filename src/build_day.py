# -*- coding: utf-8 -*-
"""Сборка одного дня: подложка под каждый кадр, вычитка, текст поверх.

От build_week отличается тем, что визуальный язык и предмет берутся не из
общей таблицы по дням, а из самого кадра. Причина простая: внутри дня
предмет один и тот же гриб, и если попросить у модели четыре раза одно и
то же, выйдут четыре одинаковых кадра. Поэтому каждый кадр называет свой
ракурс сам — целый гриб, две кучки рядом, чашка с осадком, стакан молока.

    python build_day.py content/day_mane.yaml
    python build_day.py content/day_mane.yaml --compose   # только сборка

Букв на подложке нет: их рисует PIL. Модель на длинной фразе ломает
орфографию, а вычитать её нечем — вычитчик читает изображение той же
моделью и её же опечатку не видит.
"""
import re
import sys
import time
from pathlib import Path

import yaml
from PIL import Image

import fullgen as F
import generate as gen
import looks as L
import overlays as O
import verify_frame as V
from config import CONTENT_DIR, OUT_DIR



# Что дописывается к промпту, когда у кадра есть фото-референс упаковки.
#
# Первая версия говорила только «сохрани эту банку и не рисуй читаемых
# букв» — и получила два дефекта сразу. Банка выходила как наклейка:
# студийный свет на ней, свет сцены вокруг, тени под ней нет. А запрет
# на буквы прямо спорил с требованием сохранить этикетку, на которой
# буквы есть.
#
# Поэтому здесь две вещи по отдельности: упаковка держится точно, а свет,
# тень, масштаб и резкость подчиняются сцене. Запрет на текст оставлен
# только для того, что НЕ является этикеткой товара.
REF_NOTE = """
The attached photo is a studio shot of my real product, given as a design
reference only. Do not paste it into the scene.

Photograph that product AGAIN inside the scene above, as one continuous
photograph: same camera, same eye level, same three-quarter direction as
everything else on the table, slightly turned and off-centre. It shares the
scene's optics — same lens, same shallow depth of field, same grain and
white balance — so its edges fall off softly like every other object. No
crisp cut-out edge, no halo, no sticker flatness.

The jar is NOT the hero of the frame. It stands a little back, beside or
behind the main action, partly outside the plane of focus, so its label
reads as colour and shape rather than as a catalogue front. Part of it may
be cropped or overlapped by another object — that is good, it means the jar
lives in the room.

Keep only the product design: squat proportions, tall white ribbed cap,
terracotta label with the tree emblem and the two side windows. The studio
backdrop, the glass stand and the studio lighting stay in the reference.

Exactly ONE jar, cap on. Contemporary editorial photography shot today, not
a 2000s catalogue composite. Add no lettering of your own anywhere.
"""


def draw_bg(t: dict, cfg: dict, looks: dict, outdir: Path, tok: str,
            tries=3) -> bool:
    dest = outdir / f"{t['key']}.png"
    if dest.exists():
        print(f"  · {t['key']}: підкладка вже є", flush=True)
        return True
    # Запрет людей вешается только на предметные языки. У живых он снят:
    # сторис — формат личный, и предметка в нём читается как реклама.
    look = looks[t["look"]]
    neg = cfg["negative"]
    if not look.get("people"):
        neg += " " + cfg.get("negative_still", "")
    # {jar} у subject → фірмова банка з looks.yaml. Без цього кожен кадр
    # малює свій посуд, і в одному дні стоять три різні банки.
    subject = t["subject"].replace("{jar}", cfg.get("jar", "a plain jar"))
    prompt = L.TEMPLATE.format(
        subject=" ".join(subject.split()),
        look=" ".join(look["prompt"].split()),
        negative=" ".join(neg.split()))
    # Референс упаковки. Описать банку словами не вышло трижды: форма,
    # крышка и этикетка каждый раз выходили чужими. Приложенное фото
    # модель держит точно — механика та же, что на товарных кадрах.
    ref = t.get("ref")
    if ref:
        prompt += " " + " ".join(REF_NOTE.split())

    for n in range(1, tries + 1):
        ok = (F.draw_ref(prompt, OUT_DIR / "real" / "all" / ref, tok, dest)
              if ref else F.draw_raw(prompt, tok, dest))
        if not ok:
            time.sleep(5)
            continue
        seen = V.check(dest, [], tok).get("seen", {})
        lines = [x for x in seen.get("text_lines", []) if x.strip()]
        # На кадре с референсом этикетка ОБЯЗАНА нести свои слова: это
        # настоящая упаковка, а не дорисовка. Браковать надо чужое —
        # никнеймы, интерфейс, выдуманную латиницу, — а не название
        # товара. Пока правило было общим, две годные попытки ушли в брак
        # именно за то, ради чего референс и прикладывали.
        if ref:
            allowed = re.split(r"[\s,.–—-]+",
                               (t.get("topic", "") + " лісовик мелений "
                                "цілий капсули г").lower())
            lines = [x for x in lines
                     if not all(w in allowed or w.isdigit()
                                for w in re.split(r"[\s,.–—-]+", x.lower()) if w and not re.fullmatch(r"\d+\w?", w))]
        if not lines:
            print(f"  ✔ {t['key']:24} {t['look']:14} з {n}-ї спроби", flush=True)
            return True
        print(f"  ~ {t['key']}: домальований текст {' | '.join(lines)[:44]}",
              flush=True)
        dest.unlink(missing_ok=True)
        time.sleep(5)
    print(f"  ✖ {t['key']}: брак після {tries} спроб", flush=True)
    return False


def compose(items: list, outdir: Path) -> int:
    ok = 0
    for t in items:
        bg = outdir / f"{t['key']}.png"
        if not bg.exists():
            print(f"  ✖ {t['key']}: немає підкладки")
            continue
        out = O.render(Image.open(bg).convert("RGBA"), O.from_thought(t))
        out.convert("RGB").save(outdir / f"{t['key']}.jpg", "JPEG", quality=91)
        ok += 1
    print(f"\nзібрано кадрів: {ok} із {len(items)}")
    return ok


def sheet(items: list, outdir: Path) -> None:
    """Лист на четыре кадра: день смотрят подряд, а не по одному."""
    shots = [Image.open(outdir / f"{t['key']}.jpg")
             for t in items if (outdir / f"{t['key']}.jpg").exists()]
    if not shots:
        return
    tw = 420
    th = [i.resize((tw, int(tw * i.height / i.width))) for i in shots]
    page = Image.new("RGB", (len(th) * (tw + 12) + 12, th[0].height + 24),
                     (18, 18, 20))
    for i, im in enumerate(th):
        page.paste(im, (12 + i * (tw + 12), 12))
    page.save(outdir / "_day.jpg", "JPEG", quality=92)
    print(f"лист дня: {outdir / '_day.jpg'}")


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "content/day_mane.yaml")
    items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
    cfg = yaml.safe_load((CONTENT_DIR / "looks.yaml").read_text(encoding="utf-8"))
    looks = {x["key"]: x for x in cfg["looks"]}

    outdir = OUT_DIR / path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    if "--compose" not in sys.argv:
        tok = gen.token()
        print(f"кадрів {len(items)}\n", flush=True)
        for t in items:
            draw_bg(t, cfg, looks, outdir, tok)
            time.sleep(4)
    compose(items, outdir)
    sheet(items, outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
