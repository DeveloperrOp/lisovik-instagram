# -*- coding: utf-8 -*-
"""Выгрузка каталога Лісовик из Horoshop API.

Механика взята из рабочего скрипта пайплайна карточек
(horoshop-card-pipeline/tmp/char_audit/c1_export.py):
POST auth -> token (живёт 10 мин) -> POST catalog/export/ с offset/limit.

Браузерный User-Agent обязателен: перед сайтом Cloudflare, иначе 403.
"""
import json
import urllib.error
import urllib.request

from config import BROWSER_UA, CONTENT_DIR, is_ig_safe, load_env

PAGE = 500
HARD_LIMIT = 5000


def post(api: str, endpoint: str, payload: dict) -> dict:
    req = urllib.request.Request(
        api + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": BROWSER_UA},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def fetch_all() -> list:
    e = load_env()
    api = e["HOROSHOP_API_URL"].rstrip("/") + "/"

    auth = post(api, "auth", {"login": e["HOROSHOP_LOGIN"],
                              "password": e["HOROSHOP_PASSWORD"]})
    token = (auth.get("response") or {}).get("token") or auth.get("token")
    if not token:
        raise RuntimeError(f"Не получен токен: {json.dumps(auth, ensure_ascii=False)[:300]}")
    print("авторизация ок")

    products, offset = [], 0
    while offset < HARD_LIMIT:
        rr = post(api, "catalog/export/", {"token": token, "offset": offset, "limit": PAGE})
        batch = (rr.get("response") or {}).get("products") or []
        if not batch:
            break
        products += batch
        print(f"  offset {offset} -> +{len(batch)} (всего {len(products)})")
        offset += len(batch)
    return products


def main():
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    products = fetch_all()

    raw_path = CONTENT_DIR / "catalog_raw.json"
    raw_path.write_text(json.dumps(products, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nсырой экспорт -> {raw_path.name} ({len(products)} позиций)")

    if not products:
        print("ПУСТО — проверь доступы и endpoint")
        return

    print("\n--- поля первого товара ---")
    for k, v in products[0].items():
        preview = json.dumps(v, ensure_ascii=False)
        print(f"  {k}: {preview[:120]}")

    banned = [p for p in products if not is_ig_safe(json.dumps(p, ensure_ascii=False))]
    print(f"\nвсего: {len(products)} | под запретом для IG: {len(banned)}")


if __name__ == "__main__":
    main()
