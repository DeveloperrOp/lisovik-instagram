# -*- coding: utf-8 -*-
"""Сборка контент-плана: каждый день — про один продукт.

Четыре сторис дня работают на одну тему: утром объясняем, днём показываем
как употреблять, вечером — сам товар, ночью — ошибка, сравнение или отзыв.
Иначе выходит, что утром рассказываем про ежовик, а вечером продаём чагу.

Темы берутся из content/types/*.yaml, товары — из каталога.
Если тем по продукту дня не хватает, добираем общие.

    python build_plan.py           # 4 недели
    python build_plan.py 8
"""
import json
import re
import sys
from collections import defaultdict

import yaml

from config import CONTENT_DIR, is_mix

TYPES_DIR = CONTENT_DIR / "types"
DEFAULTS = CONTENT_DIR / "defaults.yaml"
PRODUCTS = CONTENT_DIR / "products.json"
OUT = CONTENT_DIR / "content_plan.yaml"

SLOT_NAMES = ["morning", "day", "evening", "night"]
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

TEXT_FIELDS = ("headline", "body", "tip", "wrong", "right", "why",
               "steps", "options", "quote", "product_hint")


# Форма товару має збігатися з тим, про що говорять теми дня.
# Інакше зранку розповідаємо «додай ложку порошку», а ввечері продаємо капсули.
FORM_WORDS = {
    "порош": ("Мелений", "Порошок", "Молотий"),
    "мелен": ("Мелений", "Порошок", "Молотий"),
    "ложк":  ("Мелений", "Порошок", "Молотий"),
    "капсул": ("Капсули", "Екстракт у капсулах"),
    "таблет": ("Таблетки",),
    "цілі":  ("Цілий",),
    "цілу":  ("Цілий",),
    "куски": ("Цілий",),
    "заварю": ("Цілий", "Мелений", "Чай трав'яний розсипний"),
    "настій": ("Цілий", "Мелений"),
    "флакон": ("Рідкий екстракт",),
    "накрапай": ("Рідкий екстракт",),
}


def wanted_forms(day_items) -> tuple:
    """Яку форму згадують теми дня. Порожньо — форма не важлива."""
    txt = " ".join(
        str(s.get(k, "")) for s in day_items
        for k in ("headline", "body", "tip", "steps", "wrong", "right", "why")
    ).lower()
    hits = []
    for word, forms in FORM_WORDS.items():
        if word in txt:
            hits.extend(forms)
    return tuple(dict.fromkeys(hits))


def load_promotable() -> list:
    if not PRODUCTS.exists():
        return []
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    return [p for p in data["products"]
            if p.get("visible") and p.get("ig_safe") and p.get("in_stock")
            and p.get("images")]


def item_text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in TEXT_FIELDS).lower()


def load_banks() -> dict:
    banks = {}
    for path in sorted(TYPES_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        banks[data["type"]] = list(data["items"])
    return banks


def all_variants(day_themes: dict):
    """Все варианты тем: базовые плюс те, что перечислены в rotate."""
    out = []
    for day, cfg in day_themes.items():
        for v in (cfg.get("rotate") or [cfg]):
            out.append((day, v["name"], v.get("keys") or []))
    return out


_KEY_RE = {}


def theme_of(item: dict, variants) -> str:
    """Имя темы, к которой относится материал. Пусто — значит общий.

    Ключи сверяем ПО НАЧАЛУ СЛОВА. Подстрочный поиск подводил: ключ «трав»
    для чая ловил «пере-трав-лює», и тексты про целлюлозу уезжали в чайный
    день. Та же ловушка, что «ці-кави-ть» у кофе и «пуб-лікує-мо» у лечения.
    """
    txt = item_text(item)
    for _, name, keys in variants:
        for k in keys:
            rx = _KEY_RE.get(k)
            if rx is None:
                rx = _KEY_RE[k] = re.compile(r"\b" + re.escape(k), re.I)
            if rx.search(txt):
                return name
    return ""


def build_product_pool(promotable: list, defaults: dict) -> dict:
    """Товары, разложенные по дням-темам."""
    headlines = defaults["product_headlines"]
    scenes = defaults["product_scenes"]
    themes = defaults["day_themes"]

    def consistent(p) -> bool:
        nums = re.findall(r"\d+", p.get("packing") or "")
        return not nums or any(n in p["name"] for n in nums)

    def form_matches_name(p) -> bool:
        """Назва картки і форма модифікації не мають сперечатися."""
        nl, f = p["name"].lower(), (p.get("form") or "").lower()
        if "таблет" in nl and "порош" in f:
            return False
        if "порош" in nl and "таблет" in f:
            return False
        if "капсул" in nl and ("порош" in f or "мелен" in f):
            return False
        return True

    best, skipped_mix, skipped_myc = {}, 0, 0
    for p in promotable:
        # Миксы: на фото курса видны все банки состава, включая запрещённые
        if is_mix(p["name"], p["category"]):
            skipped_mix += 1
            continue
        # Мицелий: рубрика «корисне» честно советует искать плодовое тело,
        # продавать в тех же сторис мицелий — прямое противоречие
        if "міцел" in p["name"].lower():
            skipped_myc += 1
            continue
        if not form_matches_name(p):
            continue
        key = p["name"]
        if key not in best or (consistent(p) and not consistent(best[key])):
            best[key] = p

    pool = defaultdict(list)      # ключ — категорія товару
    used = defaultdict(int)
    for p in sorted(best.values(), key=lambda x: x["price"] or 0):
        cat = p["category"].split("/")[-1]

        key = next((k for k in headlines if k.lower() in cat.lower()), None)
        if not key:
            key = next((k for k in headlines if k.lower() in p["name"].lower()), None)
        if not key:
            continue
        variants = headlines[key]
        headline = min(variants, key=lambda v: used[v])
        used[headline] += 1

        bits = [b for b in (p.get("form"), p.get("packing")) if b]
        pool[cat].append({
            "headline": headline,
            "subline": (" · ".join(bits) or p["display_name"])[:44],
            "scene": scenes[len(pool[cat]) % len(scenes)],
            "product_hint": p["display_name"],
            "article": p["article"],
            "photo_url": p["images"][0],
            "form": p.get("form", ""),
        })
    return pool, skipped_mix, skipped_myc


def main():
    weeks = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    defaults = yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))
    themes = defaults["day_themes"]
    night_rot = defaults["night_rotation"]
    manual = set(defaults.get("manual_types") or [])

    promotable = load_promotable()
    banks = load_banks()
    products, skip_mix, skip_myc = build_product_pool(promotable, defaults)

    if skip_mix:
        print(f"  (пропущено міксів: {skip_mix})")
    if skip_myc:
        print(f"  (пропущено міцелію: {skip_myc})")

    # раскладываем темы по ИМЕНИ темы (Рейші, Шиїтаке, Спіруліна...),
    # а не по дню: один день может нести разные темы в разные недели
    variants = all_variants(themes)
    by_theme = defaultdict(lambda: defaultdict(list))
    common = defaultdict(list)
    for kind, items in banks.items():
        for it in items:
            name = theme_of(it, variants)
            if name:
                by_theme[name][kind].append(it)
            else:
                common[kind].append(it)

    cursor = defaultdict(int)
    stories, borrowed = [], 0
    form_misses = []

    used_ids = set()

    def _key(it):
        return (it.get("headline") or it.get("quote", ""), it.get("tip", ""))

    def take(theme_name: str, kind: str):
        """Тема дня, потом общая, и только в крайнем случае — повтор.

        Своих тем под конкретный гриб мало: на «ежовик» их одна-две, а слотов
        за месяц четыре. Раньше сборщик крутил их по кругу — выходило, что одна
        и та же инструкция шла все четыре недели. Теперь, исчерпав профильные,
        добираем общие: они тоже полезны и не ломают фокус дня так сильно,
        как дословный повтор.
        """
        nonlocal borrowed
        for pool, is_own in ((by_theme[theme_name].get(kind) or [], True),
                             (common.get(kind) or [], False)):
            for it in pool:
                if _key(it) not in used_ids:
                    used_ids.add(_key(it))
                    if not is_own:
                        borrowed += 1
                    return it, is_own
        # всё исчерпано — берём по кругу, но об этом отчитаемся
        pool = (by_theme[theme_name].get(kind) or []) + (common.get(kind) or [])
        if not pool:
            return None, False
        it = pool[cursor[(theme_name, kind)] % len(pool)]
        cursor[(theme_name, kind)] += 1
        return it, False

    def theme_for(day, week):
        """Тема дня. Деякі дні чергуються по тижнях, щоб не змішувати
        два продукти в одному дні."""
        cfg = themes[day]
        rot = cfg.get("rotate")
        return rot[(week - 1) % len(rot)] if rot else cfg

    for w in range(1, weeks + 1):
        for day in DAYS:
            cfg = theme_for(day, w)
            kinds = [k if k != "night" else night_rot[day]
                     for k in defaults["day_slots"]]
            for slot_i, kind in enumerate(kinds):
                if kind == "product":
                    # Категорії в конфізі задані коротко («Їжовик»), а в каталозі
                    # вони повні («Їжовик гребінчастий») — звіряємо входженням
                    cats = [c.lower() for c in (cfg.get("categories") or [])]
                    pool = [x for cat, lst in products.items()
                            if any(c in cat.lower() for c in cats)
                            for x in lst] if cats else []
                    if not pool:      # загальний день — беремо будь-що
                        pool = [x for lst in products.values() for x in lst]
                    if not pool:
                        continue
                    # беремо товар тієї форми, про яку говорять теми цього дня
                    forms = wanted_forms([s for s in stories
                                          if s["week"] == w and s["day"] == day])
                    # Пріоритет: своя категорія + потрібна форма -> своя
                    # категорія будь-якої форми -> тільки потім чуже.
                    # Чужий товар у дні гірший за розбіжність у формі.
                    matched = [x for x in pool if x.get("form") in forms] if forms else []
                    src_pool = matched or pool
                    if not matched and forms and pool:
                        form_misses.append(
                            f"{day} тиждень {w} ({cfg['name']}): немає форми "
                            f"{'/'.join(forms)}, беремо іншу")
                    item = src_pool[cursor[("prod", day)] % len(src_pool)]
                    cursor[("prod", day)] += 1
                    own = True
                else:
                    item, own = take(cfg["name"], kind)
                    if item is None:
                        continue

                entry = {
                    "id": f"w{w}-{day}-{SLOT_NAMES[slot_i]}",
                    "week": w, "day": day, "slot": SLOT_NAMES[slot_i],
                    "kind": kind,
                    "theme": cfg["name"],
                    "mode": "manual" if kind in manual else "auto",
                    "scene": item["scene"],
                }
                for f in ("headline", "subline", "body", "tip", "wrong", "right",
                          "why", "claim", "truth", "steps", "options", "quote",
                          "author", "product_hint", "article", "photo_url"):
                    if item.get(f):
                        entry[f] = item[f]
                stories.append(entry)

    plan = {
        "meta": {"weeks": weeks, "lang": "ua",
                 "structure": "день = один продукт"},
        "defaults": {k: defaults[k] for k in
                     ("cta", "disclaimer", "negative", "style", "slots")},
        "stories": stories,
        "reels": [{"id": f"w{w}-reel-{d}", "week": w, "day": d, "source": ""}
                  for w in range(1, weeks + 1) for d in defaults["reels_days"]],
        "feed": [{"id": f"w{w}-feed-{d}", "week": w, "day": d, "headline": ""}
                 for w in range(1, weeks + 1) for d in defaults["feed_days"]],
    }
    OUT.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False,
                                  width=95), encoding="utf-8")

    print(f"тижнів: {weeks} | сторіс: {len(stories)}")
    if form_misses:
        print(f"  форма не збіглася: {len(form_misses)}")
        for fm in form_misses[:5]:
            print("   ⚠", fm)
    print(f"загальних тем замість профільних: {borrowed}")

    print("\n--- тиждень 1 по днях ---")
    for day in DAYS:
        items = [s for s in stories if s["week"] == 1 and s["day"] == day]
        print(f"\n  {day.upper()} — {themes[day]['name']}")
        for s in items:
            mark = "  (руками)" if s["mode"] == "manual" else ""
            head = s.get("headline") or s.get("quote", "")[:34]
            print(f"    {s['slot']:8} {s['kind']:8} {head[:42]}{mark}")

    seen, dupes = defaultdict(set), 0
    for s in stories:
        key = (s.get("headline") or s.get("quote", ""), s.get("subline", ""))
        if key in seen[s["kind"]]:
            dupes += 1
        seen[s["kind"]].add(key)
    print(f"\nповних дублікатів: {dupes}")
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
