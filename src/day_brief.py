# -*- coding: utf-8 -*-
"""Бриф дня: что болит, что правда, что продаём — по ОДНОМУ продукту.

Ярик: «мне не нужно универсальных решений, мне нужен процесс, который
под каждый день делает уникальный текст».

Причина, по которой тексты выходили одинаковыми, механическая: я писал
их из головы. А в голове по всем семи продуктам лежит примерно одно и
то же — «полезный гриб, есть вещества, пейте курсом». Отсюда и кадры,
про которые нельзя понять, чага это или ежовик.

Уникальность не берётся из старания. Она берётся из того, что у чаги и
у ежовика РАЗНЫЕ жалобы в отзывах:

    чага     «На вкус настой как если деревяшку вымочили в воде»
    їжовик   «Пропил 2 курса, ни каких изменений. Что пил, что не пил»

Пока бриф собирается машинно, день не может выйти общим: он стоит на
цитатах, которые есть только у этого продукта.

    python day_brief.py чага
    python day_brief.py їжовик --full
"""
import json
import re
import sys

from config import CONTENT_DIR, OUT_DIR

VOICE = CONTENT_DIR / "voice_lines.md"
BRIEFS = OUT_DIR / "briefs"

# Как продукт зовётся в отзывах, в каталоге и в ресёрче — три разных языка
PRODUCTS = {
    "їжовик": {"voice": r"їжовик|ежовик|левова грива|грива лева|hericium",
               "catalog": "Їжовик", "science": "їжовик|ежовик"},
    "чага": {"voice": r"чаг|inonotus", "catalog": "Чага",
             "science": "чага"},
    "кордицепс": {"voice": r"кордицепс|cordyceps", "catalog": "Кордицепс",
                  "science": "кордицепс"},
    "рейші": {"voice": r"рейші|рейши|ganoderma", "catalog": "Рейші",
              "science": "рейші"},
    "ашваганда": {"voice": r"ашваганд|withania", "catalog": "Ашваганда",
                  "science": "ашваганд"},
    "спіруліна": {"voice": r"спірулін|хлорел", "catalog": "Спіруліна",
                  "science": "спірулін|хлорел"},
}


def voice_rows(rx: str) -> list:
    rows = [l.strip() for l in VOICE.read_text(encoding="utf-8").splitlines()
            if l.startswith("[")]
    out = []
    for l in rows:
        if not re.search(rx, l, re.I):
            continue
        kind = re.match(r"\[(\w+)\]", l).group(1)
        quote = re.search(r"«(.+?)»", l)
        behind = re.search(r"за цим стоїть:\s*(.+)$", l)
        out.append({"kind": kind,
                    "quote": quote.group(1) if quote else "",
                    "behind": (behind.group(1) if behind else "")[:260]})
    return out


def catalog_rows(needle: str) -> list:
    items = json.loads((CONTENT_DIR / "catalog_raw.json").read_text(
        encoding="utf-8"))
    seen, out = set(), []
    for p in items:
        ch = p.get("characteristics") or {}
        sk = (ch.get("h_1_sklad") or {}).get("ua", "")
        if needle not in sk or len(sk) > 110:
            continue
        pres = ((p.get("presence") or {}).get("value") or {}).get("ua", "")
        # «Немає в наявності» містить «наявн» — перевіряти треба на «Немає»
        if pres.lower().startswith("нема"):
            continue
        forma = ((ch.get("h_1_forma_produktu") or {}).get("value")
                 or {}).get("ua", "")
        key = (forma, sk)
        if key in seen:
            continue
        seen.add(key)
        out.append({"forma": forma, "sklad": sk})
    return out


def science_rows(rx: str) -> list:
    out = []
    for name in ("science.json", "science3.json"):
        path = OUT_DIR / name
        if not path.exists():
            continue
        for f in json.loads(path.read_text(encoding="utf-8")).get("findings", []):
            if re.search(rx, f.get("product", ""), re.I):
                out.append({k: f.get(k, "") for k in
                            ("compound", "measured", "population",
                             "duration", "source")})
    return out


def brief(key: str, full=False) -> dict:
    p = PRODUCTS[key]
    v = voice_rows(p["voice"])
    data = {"product": key,
            "voice": v,
            "catalog": catalog_rows(p["catalog"]),
            "science": science_rows(p["science"])}

    print(f"\n{'=' * 62}\nБРИФ ДНЯ: {key.upper()}\n{'=' * 62}")

    order = ["objection", "drop", "tried", "quote", "word"]
    print(f"\nЩО БОЛИТЬ — {len(v)} рядків живої мови")
    for kind in order:
        rows = [x for x in v if x["kind"] == kind]
        if not rows:
            continue
        print(f"\n  [{kind}] {len(rows)}")
        for r in rows[: (99 if full else 3)]:
            print(f"    «{r['quote'][:150]}»")
            if full and r["behind"]:
                print(f"       → {r['behind'][:150]}")

    print(f"\nЩО ПРОДАЄМО — {len(data['catalog'])} форм у наявності")
    for c in data["catalog"]:
        print(f"    {c['forma']:18} {c['sklad'][:78]}")

    print(f"\nЩО ПРАВДА — {len(data['science'])} знахідок у ресьорчі")
    for f in data["science"][: (99 if full else 4)]:
        print(f"    {f['compound'][:74]}")
        print(f"      міряли: {f['measured'][:88]}")
        print(f"      на кому: {f['population'][:88]}")

    BRIEFS.mkdir(parents=True, exist_ok=True)
    (BRIEFS / f"{key}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nзбережено: {BRIEFS / f'{key}.json'}")
    return data


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in PRODUCTS:
        print("продукти:", ", ".join(PRODUCTS))
        return 1
    brief(sys.argv[1], "--full" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
