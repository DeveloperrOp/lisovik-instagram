# -*- coding: utf-8 -*-
"""Чи всі товари тижня є в наявності.

20.09 цілий день сторіс був зроблений про екстракт агаріка 10:1, якого
немає в наявності в жодній фасовці й, за словами власника, не буде.
Наявність я дивився на етапі вибору кандидатів, а коли брав конкретний
товар і качав фото — не перевірив ще раз. День довелось переписувати.

    python check_stock.py content/day5_*.yaml
    python check_stock.py --week 5

Перевіряється КОНКРЕТНА позиція: у шапці кожного файлу дня лежить рядок
«# product: <посилання>», і наявність дивиться саме на неї. Перевірка за
назвою товару взагалі не годиться — у агаріка чотири форми були в
наявності, а саме екстракт, про який був день, ні.
"""
import glob
import json
import re
import sys
from pathlib import Path

import yaml

from config import CONTENT_DIR

# Слова, за якими topic звести до кореня назви в каталозі. Каталог веде
# назви російською, а topic — українською, тому зіставляємо вручну.
ALIAS = {
    "лисичка": "лисичка", "веселка": "весёлка", "майтаке": "майтаке",
    "агарік": "агарик", "траметес": "траметес", "хлорела": "хлорелл",
    "immunity": "immunity", "їжовик": "ежовик", "чага": "чага",
    "кордицепс": "кордицепс", "рейші": "рейши", "шиїтаке": "шиитаке",
    "ашваганда": "ашваганд", "спіруліна": "спирулин", "тремела": "тремел",
    "трійчатка": "тройчатка", "трібулус": "трибулус", "гінкго": "гинкго",
    "женьшень": "женьшень", "сереноа": "сереноа", "вітекс": "витекс",
    "мака": "мака", "омега": "омега", "магній": "магний",
}


def in_stock(p: dict) -> bool:
    v = ((p.get("presence") or {}).get("value") or {}).get("ua", "")
    return bool(v) and not v.lower().startswith("нема")


def root(topic: str) -> str:
    low = topic.lower()
    for k, v in ALIAS.items():
        if k in low:
            return v
    return re.split(r"[ ,]", low)[0]


def product_url(path: Path) -> str:
    """Посилання на конкретну позицію з шапки файлу дня."""
    for ln in path.read_text(encoding="utf-8").splitlines()[:6]:
        if ln.startswith("# product:"):
            return ln.split(":", 1)[1].strip()
    return ""


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--week" in sys.argv:
        n = sys.argv[sys.argv.index("--week") + 1]
        args = sorted(glob.glob(str(CONTENT_DIR / f"day{n}_*.yaml")))
    if not args:
        print("вкажи файли: python check_stock.py content/day5_*.yaml")
        return 1

    cat = json.loads((CONTENT_DIR / "catalog_raw.json").read_text(
        encoding="utf-8"))
    by_link = {(p.get("link") or "").rstrip("/"): p for p in cat}
    bad = 0
    for f in args:
        path = Path(f)
        th = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
        topic = th[0].get("topic", "?")
        name = path.stem
        url = product_url(path)

        if not url:
            # Без прив'язки лишається тільки груба перевірка за назвою:
            # вона пропустила екстракт агаріка, бо інші форми того ж
            # гриба були в наявності. Тому це попередження, а не «ок».
            key = root(topic)
            live = [p for p in cat
                    if key in ((p.get("title") or {}).get("ru") or "").lower()
                    and in_stock(p)]
            bad += 1
            print(f"  ⚠ {name:18} {topic}: немає рядка «# product:» — "
                  f"перевірено лише за назвою, у наявності {len(live)}")
            continue

        p = by_link.get(url.rstrip("/"))
        if not p:
            bad += 1
            print(f"  ⛔ {name:18} {topic}: позиції немає в каталозі")
            print(f"       {url}")
            continue
        t = ((p.get("title") or {}).get("ru") or "")[:52]
        if not in_stock(p):
            bad += 1
            pres = ((p.get("presence") or {}).get("value") or {}).get("ua", "")
            print(f"  ⛔ {name:18} {topic}: {pres}")
            print(f"       {t}")
            continue
        print(f"  ✔ {name:18} {topic}: {p.get('price')} грн — {t}")

    print()
    if bad:
        print(f"⛔ проблемних днів: {bad} — замінити товар або поправити рядок "
              f"«# product:»")
        return 1
    print("усі позиції тижня є в наявності")
    return 0


if __name__ == "__main__":
    sys.exit(main())
