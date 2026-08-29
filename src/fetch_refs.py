# -*- coding: utf-8 -*-
"""Референсы упаковок из каталога — с защитой от мухомора.

Зачем отдельный файл. Я скачивал референсы разовым скриптом и фильтровал
по названию гриба в составе. На кордицепсе и рейши это привело к тому,
что скачалась карточка СМЕСИ, в составе которой первым пунктом стоит
«Мухомор червоний (Amanita muscaria) 20%».

Мухомор не идёт в Instagram никогда: категория Entheogens, бан каскадит
на весь Business Manager. Ловить его надо ДО выбора фото, а не после, и
правило должно жить в коде, а не в моей памяти.

    python fetch_refs.py            # показать, что скачается
    python fetch_refs.py --write    # скачать

Берётся последнее фото карточки: в этом каталоге оно студийное, на белом,
без наложенного текста. Кадры с текстом (первые в галерее) для референса
не годятся — модель тащит чужой заголовок в сцену.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from config import CONTENT_DIR, OUT_DIR

DEST = OUT_DIR / "real" / "all"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Ни при каких условиях. Проверяется по составу, а не по названию товара:
# в смесях мухомор стоит в составе, а в названии его может не быть
BANNED = re.compile(r"мухомор|amanita|пантерн|мікродоз", re.I)

WANT = {"їжовик": "m9", "чага": "c9", "кордицепс": "cord",
        "рейші": "reishi", "шиїтаке": "shii", "ашваганда": "ashwa"}


def rows() -> list:
    items = json.loads((CONTENT_DIR / "catalog_raw.json").read_text(
        encoding="utf-8"))
    out, seen = [], set()
    for p in items:
        ch = p.get("characteristics") or {}
        sk = (ch.get("h_1_sklad") or {}).get("ua", "")
        if not sk or BANNED.search(sk):
            continue
        # монотовар, а не смесь: у смеси состав длинный и с процентами
        if sk.count(",") > 2 or "%" in sk:
            continue
        pres = ((p.get("presence") or {}).get("value") or {}).get("ua", "")
        if pres.lower().startswith("нема"):
            continue
        imgs = p.get("images") or []
        if len(imgs) < 8:
            continue
        for word, tag in WANT.items():
            if word in sk.lower() and tag not in seen:
                seen.add(tag)
                out.append({"tag": tag, "sklad": sk, "url": imgs[-1]})
    return out


def main() -> int:
    write = "--write" in sys.argv
    DEST.mkdir(parents=True, exist_ok=True)
    for r in rows():
        dest = DEST / f"{r['tag']}.jpg"
        mark = "є" if dest.exists() else ("качаю" if write else "буде")
        print(f"  {r['tag']:8} {mark:6} {r['sklad'][:66]}")
        if not write or dest.exists():
            continue
        req = urllib.request.Request(r["url"], headers={"User-Agent": UA})
        dest.write_bytes(urllib.request.urlopen(req, timeout=40).read())
    print("\nмухомор і суміші з ним відсіяні за складом, не за назвою")
    return 0


if __name__ == "__main__":
    sys.exit(main())
