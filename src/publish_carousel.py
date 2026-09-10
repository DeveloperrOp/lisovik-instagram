# -*- coding: utf-8 -*-
"""Публікація каруселі у стрічку Instagram і Facebook.

Кадри й підпис бере з out/<набір>/, куди їх кладе post_carousel.py.

    python publish_carousel.py post_osnova --dry-run   # що і куди піде
    python publish_carousel.py post_osnova             # IG + FB
    python publish_carousel.py post_osnova --no-fb     # тільки Instagram

Інстаграм збирає карусель у три кроки: контейнер на КОЖЕН кадр із
прапорцем is_carousel_item, потім батьківський контейнер типу CAROUSEL зі
списком дітей і підписом, і аж тоді публікація. Фейсбук інакше: фото
завантажуються неопублікованими, а пост у стрічці посилається на їхні id
через attached_media. Спільного коду тут майже немає, тому дві функції.

Порядок кадрів — той самий, що у файлі набору: перший кадр стає обкладинкою.
"""
import json
import sys
from pathlib import Path

import yaml

import manifest as mf
import publish as P
from config import CONTENT_DIR, OUT_DIR

MAX_ITEMS = 10          # ліміт каруселі в Instagram


def frames(stem: str) -> list:
    """Кадри набору в порядку файлу — обкладинка перша."""
    path = CONTENT_DIR / f"{stem}.yaml"
    items = yaml.safe_load(path.read_text(encoding="utf-8"))["thoughts"]
    out = []
    for t in items:
        jpg = OUT_DIR / stem / f"{t['key']}.jpg"
        if jpg.exists():
            out.append(jpg)
        else:
            print(f"  ✖ немає кадру {jpg.name}")
    return out


def publish_ig(urls: list, caption: str) -> str:
    kids = []
    for i, url in enumerate(urls, 1):
        cid = P.api(f"{P.IG_USER_ID}/media",
                    {"image_url": url, "is_carousel_item": "true",
                     "access_token": P.IG_TOKEN}, "POST")["id"]
        P.wait_ready(cid)
        print(f"  · кадр {i}/{len(urls)} готовий")
        kids.append(cid)

    parent = P.api(f"{P.IG_USER_ID}/media",
                   {"media_type": "CAROUSEL", "children": ",".join(kids),
                    "caption": caption, "access_token": P.IG_TOKEN},
                   "POST")["id"]
    P.wait_ready(parent)
    return P.api(f"{P.IG_USER_ID}/media_publish",
                 {"creation_id": parent, "access_token": P.IG_TOKEN},
                 "POST")["id"]


def publish_fb(urls: list, caption: str, ptoken: str) -> str:
    ids = []
    for i, url in enumerate(urls, 1):
        r = P.api(f"{P.FB_PAGE_ID}/photos",
                  {"url": url, "published": "false", "access_token": ptoken},
                  "POST")
        ids.append(r["id"])
        print(f"  · фото {i}/{len(urls)} завантажено")

    params = {"message": caption, "access_token": ptoken}
    for i, mid in enumerate(ids):
        params[f"attached_media[{i}]"] = json.dumps({"media_fbid": mid})
    r = P.api(f"{P.FB_PAGE_ID}/feed", params, "POST")
    return r.get("post_id") or r.get("id", "")


def main() -> int:
    P.load_dotenv()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    stem = args[0] if args else "post_osnova"
    dry = "--dry-run" in sys.argv

    imgs = frames(stem)
    cap_file = OUT_DIR / stem / "caption.txt"
    if not imgs:
        print(f"✖ у out/{stem} немає жодного кадру — спершу post_carousel.py")
        return 1
    if len(imgs) > MAX_ITEMS:
        print(f"✖ кадрів {len(imgs)}, а карусель тримає {MAX_ITEMS}")
        return 1
    if not cap_file.exists():
        print(f"✖ немає підпису {cap_file}")
        return 1
    caption = cap_file.read_text(encoding="utf-8").strip()

    print(f"набір: {stem} | кадрів: {len(imgs)}")
    for i, p in enumerate(imgs, 1):
        print(f"  {i}. {p.name}  ({p.stat().st_size // 1024} КБ)")
    print(f"\nпідпис ({len(caption)} символів):\n{caption[:300]}"
          + ("…\n" if len(caption) > 300 else "\n"))

    if dry:
        print("[dry-run] нічого не опубліковано")
        return 0
    if not P.IG_TOKEN or not P.IG_USER_ID:
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID")
        return 1

    tok = mf.token()
    urls = [mf.upload_media(p, tok) for p in imgs]
    print(f"залито в сховище: {len(urls)}")

    mid = publish_ig(urls, caption)
    print(f"✔ Instagram {mid}")

    # Фейсбук не роняє запуск: інстаграмна публікація вже пройшла
    if "--no-fb" not in sys.argv:
        try:
            print(f"✔ Facebook {publish_fb(urls, caption, P.page_token())}")
        except Exception as e:
            print(f"✖ Facebook не вийшло: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
