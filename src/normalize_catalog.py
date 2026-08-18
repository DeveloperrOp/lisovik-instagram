# -*- coding: utf-8 -*-
"""Нормализация сырого экспорта Horoshop в компактный products.json для контент-плана.

Помечает товары, которые нельзя показывать в Instagram (мухомор и производные),
и считает статистику по категориям.
"""
import json
import re
from collections import Counter

from config import CONTENT_DIR, in_stock, is_ig_safe, safe_display_name

SHOP = "https://lisovik.com.ua"


def ua(field, default=""):
    """Достаёт украинское значение из мультиязычного поля Horoshop."""
    if isinstance(field, dict):
        if "ua" in field:
            return (field.get("ua") or "").strip()
        val = field.get("value")
        if isinstance(val, dict):
            return (val.get("ua") or "").strip()
        if isinstance(val, str):
            return val.strip()
    if isinstance(field, str):
        return field.strip()
    return default


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def normalize(p: dict) -> dict:
    name = ua(p.get("title")) or ua(p.get("mod_title"))
    category = ""
    parent = p.get("parent") or {}
    if isinstance(parent, dict):
        category = str(parent.get("value") or "")

    chars = p.get("characteristics") or {}
    sklad = ua(chars.get("h_1_sklad")) if isinstance(chars, dict) else ""

    images = [i for i in (p.get("images") or []) if isinstance(i, str)]

    display = safe_display_name(name)
    # Товар годится для Instagram, только если он не в бан-списке
    # И его удалось безопасно назвать
    ig_ok = is_ig_safe(f"{name} {category}") and bool(display)

    return {
        "article": p.get("article") or "",
        "name": name,
        "display_name": display,
        "category": category,
        "price": p.get("price") or 0,
        "price_old": p.get("price_old") or 0,
        "discount": p.get("discount") or 0,
        "presence": ua(p.get("presence")),
        "form": ua(p.get("formaProduktu")),
        "packing": ua(p.get("h_1_fasuwannya")),
        "images": images[:3],
        "sklad": sklad,
        "description": strip_html(ua(p.get("description")))[:600],
        "visible": bool(p.get("display_in_showcase")),
        "in_stock": in_stock(ua(p.get("presence"))),
        "ig_safe": ig_ok,
    }


def main():
    raw = json.loads((CONTENT_DIR / "catalog_raw.json").read_text(encoding="utf-8"))
    items = [normalize(p) for p in raw]

    total = len(items)
    visible = [i for i in items if i["visible"]]
    safe = [i for i in visible if i["ig_safe"]]
    banned = [i for i in visible if not i["ig_safe"]]
    # Только то, что реально можно продвигать: разрешено И есть на складе
    promotable = [i for i in safe if i["in_stock"]]

    out = {
        "shop": SHOP,
        "total": total,
        "counts": {
            "visible": len(visible),
            "ig_safe": len(safe),
            "ig_banned": len(banned),
            "promotable": len(promotable),
        },
        "products": items,
    }
    path = CONTENT_DIR / "products.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"всего {total} | в витрине {len(visible)} | "
          f"можно в IG {len(safe)} | запрещено {len(banned)}")
    print(f"МОЖНО ПРОДВИГАТЬ (разрешено + в наличии): {len(promotable)}")
    print(f"нет в наличии среди разрешённых: {len(safe) - len(promotable)}")

    print("\n--- ТОП-категории (можно продвигать) ---")
    by_cat = Counter(i["category"].split("/")[-1] for i in promotable)
    for cat, n in by_cat.most_common(25):
        print(f"  {n:3}  {cat}")

    print("\n--- ЗАПРЕЩЕНО для IG ---")
    by_banned = Counter(i["category"].split("/")[-1] for i in banned)
    for cat, n in by_banned.most_common():
        print(f"  {n:3}  {cat}")

    print("\n--- ПОЛНОСТЬЮ РАСПРОДАННЫЕ категории (не ставить в план) ---")
    cats_all = {i["category"].split("/")[-1] for i in safe}
    cats_ok = {i["category"].split("/")[-1] for i in promotable}
    for cat in sorted(cats_all - cats_ok):
        n = sum(1 for i in safe if i["category"].split("/")[-1] == cat)
        print(f"  {n:3}  {cat}")

    print("\n--- цены по тому, что можно продвигать ---")
    prices = sorted(i["price"] for i in promotable if i["price"])
    if prices:
        mid = prices[len(prices) // 2]
        print(f"  от {prices[0]} до {prices[-1]} грн, медиана {mid} грн")

    with_photo = [i for i in promotable if i["images"]]
    print(f"\nс фото: {len(with_photo)} из {len(promotable)}")


if __name__ == "__main__":
    main()
