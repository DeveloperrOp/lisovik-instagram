# -*- coding: utf-8 -*-
"""Линтер контент-плана: не пропускает в публикацию то, что нарушает
правила Meta, украинский закон о рекламе добавок и бренд-правила Лісовика.

Запуск:  python lint.py
Код возврата 1, если есть блокирующие нарушения.
"""
import json
import re
import sys

import yaml

from config import CONTENT_DIR, is_discontinued

PLAN = CONTENT_DIR / "content_plan.yaml"
PRODUCTS = CONTENT_DIR / "products.json"

# Блокирующие. Ищем по границе слова: подстрочный поиск ловил «публікуємо»
# как «лікує» и блокировал нормальный текст.
STOP_PATTERNS = (
    r"мухомор", r"\bаманіт", r"\bлотос",
    r"\bмікродоз", r"\bпсихоактив", r"\bпсиходел", r"\bнаркотик",
    r"\bгалюцин", r"\bтрип\b",
    r"\b(ви|за)?лікує", r"\b(ви|за)?лікують", r"\b(ви|за)?лікув",
    r"\bзцілю", r"\bзцілен", r"\bпрофілактик", r"\bтерапі",
    r"замість ліків", r"замінює ліки",
    r"\bдепресі", r"\bтривожн", r"\bбезсон", r"\bімунітет",
    r"паразит",                    # без \b: «протипаразитна»
    r"\bгарантован", r"100\s?%", r"\bназавжди",
    r"\bкарпат",                   # бренд-правило: не для зображень
    r"вирощено в україні", r"виготовлено в україні", r"зроблено в україні",
)

WARN_PATTERNS = (
    r"\bстрес", r"\bсон\b", r"\bенергі", r"\bсуперфуд", r"\bдетокс",
    r"\bочищенн",
)

_STOP = [re.compile(p, re.I) for p in STOP_PATTERNS]
_WARN = [re.compile(p, re.I) for p in WARN_PATTERNS]

# Бренд-правило запрещает ДОЗИРОВКУ, а не фасовку: «по 0,5 г» нельзя,
# «50 мл» на флаконе и «50 грам» в банке — обычная характеристика товара.
DOSAGE = re.compile(r"(\bпо\s+\d+[\.,]?\d*\s?(г|мг|мл)\b|\b\d+[\.,]?\d*\s?мг\b)", re.I)

MAX_HEADLINE = 32
MAX_SUBLINE = 46
MAX_STEP = 42

# Какие поля обязательны для каждого типа
REQUIRED = {
    "product": ("headline", "subline"),
    "useful": ("headline", "body"),
    "mistake": ("headline", "wrong", "right"),
    "howto": ("headline", "steps"),
    "compare": ("headline", "options"),
    "review": ("quote",),
    "myth": ("headline", "claim", "truth"),
    "ask": ("headline",),
    # старые типы, оставлены на случай переиспользования
    "fact": ("headline",),
    "mood": ("headline",),
}

MAX_BODY = 360      # длиннее — не влезает в кадр даже мелким кеглем


def check_text(text: str, where: str, errors: list, warnings: list):
    if not text:
        return
    for pat in _STOP:
        m = pat.search(text)
        if m:
            errors.append(f"{where}: заборонене «{m.group(0)}» → {text!r}")
    for pat in _WARN:
        m = pat.search(text)
        if m:
            warnings.append(f"{where}: перевір «{m.group(0)}» → {text!r}")
    if is_discontinued(text):
        errors.append(f"{where}: знято з продажу (кава/лате/какао/матча) → {text!r}")
    if DOSAGE.search(text):
        errors.append(f"{where}: дозування в кадрі заборонене → {text!r}")


def load_promotable() -> list:
    if not PRODUCTS.exists():
        return []
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    return [p for p in data["products"]
            if p.get("visible") and p.get("ig_safe") and p.get("in_stock")]


def check_stock(item: dict, promotable: list, errors: list):
    hint = (item.get("product_hint") or "").strip()
    if not hint or not promotable:
        return
    low = hint.lower()
    if not any(low in p["name"].lower() or low in p["category"].lower()
               or low in p["display_name"].lower() for p in promotable):
        errors.append(f"{item.get('id','?')}: товару «{hint}» немає в наявності")


def check_item(s: dict, promotable: list, errors: list, warnings: list):
    sid = s.get("id", "?")
    kind = s.get("kind")

    if kind not in REQUIRED:
        errors.append(f"{sid}: невідомий тип «{kind}»")
        return
    for field in REQUIRED[kind]:
        if not s.get(field):
            errors.append(f"{sid}: тип {kind} вимагає поле «{field}»")

    for field in ("headline", "subline", "quote", "body", "tip",
                  "wrong", "right", "why", "claim", "truth"):
        check_text(s.get(field, ""), f"{sid}.{field}", errors, warnings)

    body = s.get("body", "")
    if len(body) > MAX_BODY:
        warnings.append(f"{sid}.body: {len(body)} символів (>{MAX_BODY})")

    for n, step in enumerate(s.get("steps") or [], 1):
        check_text(step, f"{sid}.step{n}", errors, warnings)
        if len(step) > MAX_STEP:
            warnings.append(f"{sid}.step{n}: {len(step)} символів (>{MAX_STEP})")

    for opt in s.get("options") or []:
        check_text(opt.get("title", ""), f"{sid}.option", errors, warnings)
        check_text(opt.get("text", ""), f"{sid}.option", errors, warnings)

    head = s.get("headline", "")
    if len(head) > MAX_HEADLINE:
        warnings.append(f"{sid}.headline: {len(head)} символів (>{MAX_HEADLINE})")
    if len(s.get("subline", "")) > MAX_SUBLINE:
        warnings.append(f"{sid}.subline: задовгий")

    if kind == "howto" and len(s.get("steps") or []) != 3:
        errors.append(f"{sid}: у howto має бути рівно 3 кроки")
    if kind == "compare" and len(s.get("options") or []) != 2:
        errors.append(f"{sid}: у compare має бути рівно 2 варіанти")

    if not s.get("scene"):
        errors.append(f"{sid}: немає scene")
    if s.get("mode") not in ("auto", "manual"):
        errors.append(f"{sid}: mode має бути auto або manual")

    check_stock(s, promotable, errors)



# ---------------------------------------------------------------- узгодженість дня
# Ці перевірки зʼявились після того, як Ярик ловив руками: зранку розповідали
# про порошок, а ввечері продавали капсули; теми про рейші, а товар — лисички.
# Тепер це ловиться автоматично.

FORM_HINTS = {
    "порош": ("Мелений", "Порошок", "Молотий"),
    "мелен": ("Мелений", "Порошок", "Молотий"),
    "ложк": ("Мелений", "Порошок", "Молотий"),
    "капсул": ("Капсули", "Екстракт у капсулах"),
    "таблет": ("Таблетки",),
    "заварю": ("Цілий", "Мелений", "Чай трав'яний розсипний",
               "Чай ферментований розсипний"),
    "настій": ("Цілий", "Мелений"),
    "куски": ("Цілий",),
}


def _form_of(hint: str, promotable: list) -> str:
    low = (hint or "").lower()
    for p in promotable:
        if low and low in p["display_name"].lower():
            return p.get("form", "")
    return ""


def check_days(stories: list, promotable: list, errors: list, warnings: list):
    """День має бути про один продукт, і товар має цьому продукту відповідати."""
    by_day = {}
    for s in stories:
        by_day.setdefault((s.get("week"), s.get("day")), []).append(s)

    for (week, day), items in sorted(by_day.items(), key=lambda x: (x[0][0] or 0, str(x[0][1]))):
        theme = (items[0].get("theme") or "").lower()
        if not theme:
            continue
        stem = theme.rstrip("аиіяї")[:5]        # «Спіруліна» -> «спірул»
        tag = f"w{week}-{day}"

        prods = [s for s in items if s.get("kind") == "product"]
        for pr in prods:
            hint = (pr.get("product_hint") or "").lower()
            if stem and stem not in hint:
                errors.append(
                    f"{tag}: день «{items[0].get('theme')}», а товар «{hint[:40]}» "
                    f"— інший продукт")

            # форма товару має збігатися з тим, про що говорять тексти дня
            txt = " ".join(
                str(s.get(k, "")) for s in items
                for k in ("headline", "body", "tip", "steps", "wrong", "right")
            ).lower()
            wanted = []
            for word, forms in FORM_HINTS.items():
                if word in txt:
                    wanted.extend(forms)
            if wanted:
                form = _form_of(pr.get("product_hint", ""), promotable)
                if form and form not in wanted:
                    warnings.append(
                        f"{tag}: тексти дня про {'/'.join(sorted(set(wanted)))[:40]}, "
                        f"а товар у формі «{form}»")


def check_week_dupes(stories: list, warnings: list):
    """Одна тема двічі за тиждень — навіть у різних типах — читається як повтор."""
    stop = {"гриби", "гриба", "грибів", "просто", "тому", "через", "треба",
            "можна", "краще", "більше", "менше", "саме", "який"}

    def sig(s):
        txt = " ".join(str(s.get(k, "")) for k in
                       ("headline", "body", "tip", "claim", "truth", "why",
                        "wrong", "right", "steps", "options")).lower()
        return {w.strip("«»,.:?!—()") for w in txt.split() if len(w) > 5} - stop

    weeks = {}
    for s in stories:
        weeks.setdefault(s.get("week"), []).append(s)
    for week, items in sorted(weeks.items(), key=lambda x: x[0] or 0):
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                common = sig(items[i]) & sig(items[j])
                if len(common) >= 4:
                    same = " В ОДИН ДЕНЬ" if items[i]["day"] == items[j]["day"] else ""
                    warnings.append(
                        f"тиждень {week}{same}: «{items[i].get('headline','')[:28]}» "
                        f"~ «{items[j].get('headline','')[:28]}» ({len(common)} слів)")


def main() -> int:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    promotable = load_promotable()
    errors, warnings = [], []
    if not promotable:
        warnings.append("products.json не знайдено — перевірка наявності пропущена")

    defaults = plan.get("defaults") or {}
    neg = (defaults.get("negative") or "").lower()
    for must in ("amanita", "no people", "no dosage"):
        if must not in neg:
            errors.append(f"defaults.negative: немає обовʼязкового «{must}»")
    disc = (defaults.get("disclaimer") or "").lower()
    if "не замінює повноцінний раціон" not in disc:
        errors.append("defaults.disclaimer: немає «не замінює повноцінний раціон»")

    stories = plan.get("stories") or []
    ids = [s.get("id") for s in stories]
    if len(ids) != len(set(ids)):
        errors.append("stories: дублікати id")

    for s in stories:
        check_item(s, promotable, errors, warnings)

    check_days(stories, promotable, errors, warnings)
    check_week_dupes(stories, warnings)

    kinds = {}
    for s in stories:
        kinds[s.get("kind")] = kinds.get(s.get("kind"), 0) + 1

    print(f"перевірено сторіс: {len(stories)}")
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())))

    if warnings:
        print(f"\n--- ПОПЕРЕДЖЕННЯ ({len(warnings)}) ---")
        for w in warnings[:20]:
            print("  ⚠", w)
        if len(warnings) > 20:
            print(f"  … ще {len(warnings) - 20}")

    if errors:
        print(f"\n--- ПОМИЛКИ, публікація заблокована ({len(errors)}) ---")
        for e in errors[:30]:
            print("  ✖", e)
        if len(errors) > 30:
            print(f"  … ще {len(errors) - 30}")
        return 1

    print("\n✅ блокуючих порушень немає")
    return 0


if __name__ == "__main__":
    sys.exit(main())
