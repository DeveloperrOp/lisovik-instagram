# -*- coding: utf-8 -*-
"""Збір мови покупця з карток нашого ж сайту.

Навіщо. voice_lines.md збирався під гриби, і для чаїв, магнію, маки,
трібулуса й тремели там немає жодного рядка. Кадри під ці теми довелось
ставити на складі, а не на запереченнях — власник сказав знайти мову.

Найдешевше джерело — відгуки під нашими ж картками: вони вже написані
нашими покупцями й лежать за антиботом, який обходиться однією кукою.

    python fetch_reviews.py --list        # які товари братимемо
    python fetch_reviews.py --write       # зібрати у voice_new.md

Сторінка за антиботом: перший запит віддає JS-челендж із готовим хешем,
ставимо його кукою і просимо ще раз — та сама механіка, що в post_week.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from config import CONTENT_DIR, OUT_DIR

OUT = CONTENT_DIR / "voice_new.md"
CACHE = OUT_DIR / "reviews"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Теми, під які мови немає. Гриби сюди не входять — по них корпус є.
WANT = re.compile(r"чай|магній|омега|мака перуан|трібул|тремел|вітекс|"
                  r"сереноа|женьшень|іван-чай|арнік|щоденна основа|"
                  r"стійкий спокій|тонус і витрив", re.I)


def cookie() -> str:
    r = subprocess.run(["curl", "-s", "-A", UA, "https://lisovik.com.ua/"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    m = re.search(r'"([a-f0-9]{64})"', r.stdout or "")
    return m.group(1) if m else ""


def targets() -> list:
    items = json.loads((CONTENT_DIR / "catalog_raw.json").read_text(
        encoding="utf-8"))
    out, seen = [], set()
    for p in items:
        t = p.get("title") or {}
        name = t.get("ua", "") if isinstance(t, dict) else ""
        pres = ((p.get("presence") or {}).get("value") or {}).get("ua", "")
        link = p.get("link") or ""
        if pres.lower().startswith("нема") or not WANT.search(name):
            continue
        if not link or link in seen:
            continue
        seen.add(link)
        out.append({"name": name, "link": link})
    return out


def reviews(html: str) -> list:
    """Відгуки з картки. Розмітка Horoshop: блок j-review з текстом."""
    out = []
    for m in re.finditer(r'class="[^"]*review[^"]*"[^>]*>(.{0,1400}?)</div>',
                         html, re.S | re.I):
        frag = re.sub(r"<[^>]+>", " ", m.group(1))
        frag = re.sub(r"&[a-z#0-9]+;", " ", frag)
        frag = re.sub(r"\s+", " ", frag).strip()
        # відгук — це речення, а не підпис кнопки
        if len(frag) < 40 or not re.search(r"[а-яіїєґ]{4}", frag, re.I):
            continue
        if re.search(r"залиш|написати відгук|оцінк|рейтинг|сортув", frag, re.I):
            continue
        out.append(frag[:400])
    return out


def main() -> int:
    rows = targets()
    if "--list" in sys.argv:
        for r in rows:
            print(f"  {r['name'][:56]}")
        print(f"\nтоварів: {len(rows)}")
        return 0

    CACHE.mkdir(parents=True, exist_ok=True)
    ck = cookie()
    found, empty = [], 0
    for i, r in enumerate(rows, 1):
        slug = r["link"].rstrip("/").rsplit("/", 1)[-1]
        page = CACHE / f"{slug}.html"
        if not page.exists():
            subprocess.run(["curl", "-sL", "-A", UA, "-b",
                            f"challenge_passed={ck}", r["link"],
                            "-o", str(page)], check=False)
            time.sleep(1)
        html = page.read_text(encoding="utf-8", errors="replace")
        rev = reviews(html)
        if rev:
            found.append({"name": r["name"], "link": r["link"], "rev": rev})
            print(f"  ✔ {len(rev):2} відгуків — {r['name'][:48]}")
        else:
            empty += 1
    print(f"\nтоварів з відгуками: {len(found)} із {len(rows)}"
          f" | без відгуків: {empty}")

    if "--write" in sys.argv and found:
        lines = ["# Мова покупця: чаї, вітаміни, трави\n",
                 "# Зібрано з відгуків під нашими ж картками. Гриби сюди не\n"
                 "# входять — по них є voice_lines.md.\n"]
        for f in found:
            lines.append(f"\n## {f['name']}\n{f['link']}\n")
            for r in f["rev"]:
                lines.append(f"- «{r}»")
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print("записано:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
