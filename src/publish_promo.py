# -*- coding: utf-8 -*-
"""Публикация разовой акции: пост в ленту + сторис по дням.

Отдельно от publish.py намеренно. Тот крутится по расписанию каждые
20 минут и сейчас исправно доводит первую неделю — ломать его ради
разовой акции незачем. Здесь всё запускается руками и по одному кадру.

    python publish_promo.py --dry-run          # что и куда уйдёт
    python publish_promo.py post               # пост в ленту IG + FB
    python publish_promo.py promo-24           # сторис за 24-е
    python publish_promo.py promo-25 --no-fb   # только Instagram

Пост в ленту — третий тип контейнера, которого в publish.py не было:
там только STORIES и REELS. У ленты, в отличие от сторис, есть caption.
"""
import sys
from datetime import datetime

import yaml

import manifest as mf
import publish as P
from config import CONTENT_DIR, OUT_DIR

PLAN = CONTENT_DIR / "promo_independence.yaml"
PROMO = OUT_DIR / "promo"


def create_feed_container(image_url: str, caption: str) -> str:
    """Пост в ленту. media_type не указываем — по умолчанию IMAGE."""
    return P.api(f"{P.IG_USER_ID}/media",
                 {"image_url": image_url, "caption": caption,
                  "access_token": P.IG_TOKEN}, "POST")["id"]


def publish_feed(image_url: str, caption: str) -> str:
    cid = create_feed_container(image_url, caption)
    P.wait_ready(cid)
    return P.api(f"{P.IG_USER_ID}/media_publish",
                 {"creation_id": cid, "access_token": P.IG_TOKEN},
                 "POST")["id"]


def publish_fb_feed(image_url: str, caption: str, ptoken: str) -> str:
    """Пост в ленту страницы Facebook — сразу опубликованный, с подписью."""
    r = P.api(f"{P.FB_PAGE_ID}/photos",
              {"url": image_url, "message": caption, "published": "true",
               "access_token": ptoken}, "POST")
    return r.get("post_id") or r.get("id", "")


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    skip_fb = "--no-fb" in args
    want = [a for a in args if not a.startswith("--")]

    if not want and not dry:
        print("вкажи що публікувати: post | promo-24 | promo-25 | promo-26")
        return 1

    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    by_id = {i["id"]: i for i in plan["items"]}
    caption = plan["caption"].strip()

    targets = []
    for w in (want or ["post", "promo-24", "promo-25", "promo-26"]):
        sid = "promo-post" if w == "post" else w
        if sid not in by_id:
            print(f"✖ невідомий кадр: {w}")
            return 1
        targets.append(sid)

    if not dry and (not P.IG_TOKEN or not P.IG_USER_ID):
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID")
        return 1

    now = datetime.now(mf.KYIV)
    print(f"{now:%Y-%m-%d %H:%M} Київ\n")

    tok = None if dry else mf.token()
    ptoken = None

    for sid in targets:
        src = PROMO / f"{sid}.jpg"
        if not src.exists():
            print(f"  ✖ {sid}: немає файлу — спершу promo.py")
            continue
        is_post = by_id[sid].get("format") == "post"
        kind = "пост у стрічку" if is_post else "сторіс"

        if dry:
            print(f"  [dry] {sid} → {kind}"
                  + (f", підпис {len(caption)} символів" if is_post else ""))
            continue

        url = mf.upload_media(src, tok)
        try:
            if is_post:
                mid = publish_feed(url, caption)
            else:
                mid = P.publish_item({"kind": "STORIES", "media_url": url})
            print(f"  ✔ {sid} → IG {mid}  ({kind})")
        except Exception as e:
            print(f"  ✖ {sid}: {e}")
            continue

        # Facebook не роняет запуск: инстаграмная публикация уже прошла
        if not skip_fb:
            try:
                ptoken = ptoken or P.page_token()
                fb = (publish_fb_feed(url, caption, ptoken) if is_post
                      else P.publish_fb_story(url, ptoken))
                print(f"    ↳ FB {fb}")
            except Exception as e:
                print(f"    ↳ FB не вийшло: {str(e)[:140]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
