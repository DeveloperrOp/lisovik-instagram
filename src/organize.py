# -*- coding: utf-8 -*-
"""Одна тека, де видно все: що вийшло, що в черзі, що чекає.

Ярик: «де мені всі ці фото подивитись, щоб зрозуміти що на публікацію
відправляти… щоб усе було красиво і зрозуміло по папочках».

Раніше готове лежало в трьох теках ГОТОВЕ, ГОТОВЕ-2 і ГОТОВЕ-3, а стан
кожного кадру — тільки в маніфесті. Подивитись очима, що вже вийшло, а
що ще ні, було ніде.

Тепер усе в одному місці й розкладено за СТАНОМ, а не за тижнем:

    out/АРХІВ/
      0_ОГЛЯД.jpg              весь тиждень однією картинкою
      0-НА-ЗАТВЕРДЖЕННЯ/       поставлене на дати, але чекає твого «так»
      1-ОПУБЛІКОВАНО/          що вже вийшло в акаунт, з датою виходу
      2-У-ЧЕРЗІ/               що піде само, з датою й часом
      3-ГОТОВЕ-ЧЕКАЄ/          намальоване, але в чергу не поставлене
      4-ПОСТИ/                 пости у стрічку
      5-ВІДКЛАДЕНО/            продукт уже виходив в акаунт, чекає ротації

Імена файлів кажуть усе без відкривання:
    31.08_19-00_Чага_ЩО-БРАТИ-ПЕРШИМ.jpg

Тека збирається заново щоразу, тому її можна сміливо видаляти.

    python organize.py
"""
import re
import shutil
import sys

import yaml
from PIL import Image, ImageDraw

import manifest as mf
from config import CONTENT_DIR, OUT_DIR

DEST = OUT_DIR / "АРХІВ"
FOLDERS = ["0-НА-ЗАТВЕРДЖЕННЯ", "1-ОПУБЛІКОВАНО", "2-У-ЧЕРЗІ",
           "3-ГОТОВЕ-ЧЕКАЄ", "4-ПОСТИ", "5-ВІДКЛАДЕНО"]


def safe(text: str) -> str:
    """Имя файла из заголовка кадра: без запрещённых символов."""
    t = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip()
    return re.sub(r"\s+", "-", t)[:44]


def frames() -> list:
    """Все кадры всех наборов: файл, ключ, продукт, заголовок, слот."""
    slots = yaml.safe_load(
        (CONTENT_DIR / "defaults.yaml").read_text(encoding="utf-8"))["slots"]
    offers = {o["day"]: o for o in yaml.safe_load(
        (CONTENT_DIR / "offers.yaml").read_text(encoding="utf-8"))["offers"]}
    out = []
    # Шиїтаке з публікацій виведено — у теку майбутніх він не потрапляє.
    for path in sorted(CONTENT_DIR.glob("day*.yaml")):
        if "shiitake" in path.stem:
            continue
        items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        if not items:
            continue
        day = items[0].get("day")
        src = OUT_DIR / path.stem
        rows = [(t["slot"], t["key"], t.get("topic", ""), t["claim"])
                for t in items]
        o = offers.get(day)
        if o:
            rows.append(("night", f"{path.stem}-offer", "Лісовик", o["claim"]))
        for slot, key, topic, claim in rows:
            jpg = src / f"{key}.jpg"
            if jpg.exists():
                out.append({"file": jpg, "key": key, "topic": topic,
                            "claim": claim, "slot": slot,
                            "time": slots[slot][0], "set": path.stem})
    return out


def main() -> int:
    if DEST.exists():
        shutil.rmtree(DEST)
    for f in FOLDERS:
        (DEST / f).mkdir(parents=True)

    m = mf.load()
    # У маніфесті id виглядає як «0830-mane-dawn»: дата, набір і слот.
    # Ключ кадру («mane-what-changes») з ним не збігається, тому
    # звіряємось по парі набір+слот, а не по ключу.
    def parts(item_id):
        bits = item_id.split("-")
        return (bits[1] if len(bits) > 2 else "", bits[-1])

    # Продукти, які вже виходили в акаунт. Ярик 05.09: «в цій папці
    # продукти що вже публікували, збери в окрему папку, ми їх поки
    # відкладемо» — другий тиждень намальований на ті самі сім грибів,
    # і в теці майбутнього їм робити нічого, поки не пройде ротація.
    # Продукт беремо з id («0905-reishi-night» → reishi), а не з теми:
    # тема в маніфесті писалась по-різному («Чага» і «Чага березова»),
    # а стара тема «Чай» — це взагалі збірний кадр, не іван-чай.
    seen = set()
    published, queued, waiting = {}, {}, {}
    for i in m["items"]:
        stem, slot = parts(i["id"])
        if not stem:
            continue
        if i["status"] == "published":
            published[(stem, slot)] = i
            seen.add(stem)
        elif i["status"] == "approved":
            queued[(stem, slot)] = i
        elif i["status"] == "pending":
            waiting[(stem, slot)] = i

    counts = dict.fromkeys(FOLDERS, 0)
    sheets = {}
    for fr in frames():
        # У черзі стоїть ЛИШЕ перший набір (day_*). Другий і третій
        # мають ті самі назви продуктів, і без цієї перевірки їхні кадри
        # зараховувались би як опубліковані.
        first = fr["set"].startswith("day_")
        # «day_mane» і «day2_mane» — один продукт: префікс тижня знімаємо
        # цілком, інакше другий набір не впізнається як уже виданий.
        stem = re.sub(r"^day\d*_", "", fr["set"])
        pub = published.get((stem, fr["slot"])) if first else None
        # Відкладені перевіряємо ДО черги: другий набір має ті самі stem,
        # що й перший, і без цього його кадри читались би як поставлені.
        if pub:
            folder, when = "1-ОПУБЛІКОВАНО", (pub.get("published_at")
                                              or pub["slot_start"])[:10]
        elif stem in seen and not first:
            folder, when = "5-ВІДКЛАДЕНО", ""
        elif (que := queued.get((stem, fr["slot"]))):
            folder, when = "2-У-ЧЕРЗІ", que["slot_start"][:10]
        elif (wait := waiting.get((stem, fr["slot"]))):
            folder, when = "0-НА-ЗАТВЕРДЖЕННЯ", wait["slot_start"][:10]
        else:
            folder, when = "3-ГОТОВЕ-ЧЕКАЄ", ""
        d = f"{when[8:10]}.{when[5:7]}_" if when else ""
        name = (f"{d}{fr['time'].replace(':', '-')}_"
                f"{safe(fr['topic'])}_{safe(fr['claim'])}.jpg")
        shutil.copy2(fr["file"], DEST / folder / name)
        counts[folder] += 1
        sheets.setdefault(folder, []).append(DEST / folder / name)

    post = OUT_DIR / "post_week" / "post_week.jpg"
    if post.exists():
        shutil.copy2(post, DEST / "4-ПОСТИ" / "Товар-тижня_-20-ясна-голова.jpg")
        cap = OUT_DIR / "post_week" / "caption.txt"
        if cap.exists():
            shutil.copy2(cap, DEST / "4-ПОСТИ" / "Товар-тижня_підпис.txt")
        counts["4-ПОСТИ"] += 1

    # оглядовий лист: по рядку на стан
    rows = []
    for folder in FOLDERS:
        files = sorted(sheets.get(folder, []))[:12]
        if not files:
            continue
        tw = 150
        th = [Image.open(f).convert("RGB").resize(
            (tw, int(tw * Image.open(f).height / Image.open(f).width)))
            for f in files]
        rows.append((folder, th))
    if rows:
        h = max(i.height for _, th in rows for i in th) + 34
        page = Image.new("RGB", (12 * 158 + 20, len(rows) * h + 12), (26, 26, 28))
        d = ImageDraw.Draw(page)
        y = 8
        for folder, th in rows:
            d.text((12, y), f"{folder}  ({counts[folder]})", fill=(240, 200, 60))
            for n, im in enumerate(th):
                page.paste(im, (12 + n * 158, y + 20))
            y += h
        page.save(DEST / "0_ОГЛЯД.jpg", "JPEG", quality=88)

    print(f"тека: {DEST}\n")
    for f in FOLDERS:
        print(f"  {f:18} {counts[f]:3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
