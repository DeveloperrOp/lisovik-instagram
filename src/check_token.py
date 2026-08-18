# -*- coding: utf-8 -*-
"""Проверка готовности к публикации. Запускать до первой публикации.

    python check_token.py

Отвечает на один вопрос: можно ли уже публиковать, и если нет — чего не хватает.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

from config import GRAPH_VERSION, PROJECT_ROOT

GRAPH = f"https://graph.facebook.com/{GRAPH_VERSION}"

NEEDED_SCOPES = ("instagram_basic", "instagram_content_publish")


def load_dotenv():
    """Читает .env проекта, не перетирая уже заданное окружение."""
    p = PROJECT_ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get(url: str):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return None, json.loads(body).get("error", {}).get("message", body[:200])
        except Exception:
            return None, body[:200]


def main() -> int:
    load_dotenv()
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    ig_id = os.environ.get("IG_USER_ID", "").strip()
    bucket = os.environ.get("LISOVIK_BUCKET", "").strip()

    problems = []

    print("=== доступи ===")
    if not token:
        print("  ✖ IG_ACCESS_TOKEN не заданий")
        problems.append("токен")
    else:
        print(f"  ✔ токен заданий ({len(token)} символів)")
    print(f"  {'✔' if ig_id else '✖'} IG_USER_ID: {ig_id or 'не заданий'}")
    print(f"  {'✔' if bucket else '✖'} бакет: {bucket or 'не заданий'}")

    if not token or not ig_id:
        print("\nЗаповни .env — приклад у .env.example")
        return 1

    print("\n=== права токена ===")
    data, err = get(f"{GRAPH}/debug_token?input_token={token}&access_token={token}")
    if err:
        print(f"  ✖ {err}")
        return 1
    d = data.get("data", {})
    scopes = d.get("scopes", [])
    print(f"  застосунок: {d.get('application')}")
    print(f"  тип: {d.get('type')} | дійсний: {d.get('is_valid')}")
    exp = d.get("expires_at")
    print(f"  спливає: {'ніколи' if exp == 0 else exp}")
    print(f"  скоупи: {', '.join(scopes) or '—'}")

    missing = [s for s in NEEDED_SCOPES
               if not any(s in sc for sc in scopes)]
    if missing:
        print(f"  ✖ бракує: {', '.join(missing)}")
        problems.append("скоупи")

    print("\n=== акаунт ===")
    data, err = get(f"{GRAPH}/{ig_id}?fields=username,name&access_token={token}")
    if err:
        print(f"  ✖ {err}")
        problems.append("доступ до акаунта")
    else:
        print(f"  ✔ @{data.get('username')} — {data.get('name')}")

    print("\n=== право публікувати ===")
    data, err = get(f"{GRAPH}/{ig_id}/content_publishing_limit?access_token={token}")
    if err:
        print(f"  ✖ {err}")
        problems.append("право публікації")
    else:
        quota = (data.get("data") or [{}])[0]
        print(f"  ✔ опубліковано за 24 години: {quota.get('quota_usage', 0)} зі 100")

    print()
    if problems:
        print(f"НЕ ГОТОВО: {', '.join(problems)}")
        return 1
    print("✅ ВСЕ ГОТОВО — можна публікувати")
    return 0


if __name__ == "__main__":
    sys.exit(main())
