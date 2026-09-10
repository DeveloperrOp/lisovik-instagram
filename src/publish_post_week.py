# -*- coding: utf-8 -*-
"""Публікація поста «Товар тижня» у стрічку Instagram і Facebook.

Раніше цей пост відправляли руками з чату, і щотижня доводилось згадувати
послідовність. Тут вона одна: кадр і підпис беруться з out/post_week/,
куди їх кладе post_week.py.

    python publish_post_week.py --dry-run     # що і куди піде
    python publish_post_week.py               # IG + FB
    python publish_post_week.py --no-fb       # тільки Instagram

Пост у стрічці — контейнер без media_type (за замовчуванням IMAGE) і з
підписом; сторіс, на відміну від нього, підпису не має.
"""
import sys
from datetime import datetime

import manifest as mf
import publish as P
from config import OUT_DIR

DEST = OUT_DIR / "post_week"
IMG = DEST / "post_week.jpg"
CAP = DEST / "caption.txt"


def publish_feed(image_url: str, caption: str) -> str:
    cid = P.api(f"{P.IG_USER_ID}/media",
                {"image_url": image_url, "caption": caption,
                 "access_token": P.IG_TOKEN}, "POST")["id"]
    P.wait_ready(cid)
    return P.api(f"{P.IG_USER_ID}/media_publish",
                 {"creation_id": cid, "access_token": P.IG_TOKEN},
                 "POST")["id"]


def publish_fb_feed(image_url: str, caption: str, ptoken: str) -> str:
    r = P.api(f"{P.FB_PAGE_ID}/photos",
              {"url": image_url, "message": caption, "published": "true",
               "access_token": ptoken}, "POST")
    return r.get("post_id") or r.get("id", "")


def main() -> int:
    P.load_dotenv()
    dry = "--dry-run" in sys.argv
    skip_fb = "--no-fb" in sys.argv

    if not IMG.exists():
        print(f"✖ немає кадру {IMG} — спершу post_week.py")
        return 1
    if not CAP.exists():
        print(f"✖ немає підпису {CAP}")
        return 1
    caption = CAP.read_text(encoding="utf-8").strip()

    now = datetime.now(mf.KYIV)
    print(f"{now:%Y-%m-%d %H:%M} Київ")
    print(f"кадр:   {IMG.name} ({IMG.stat().st_size // 1024} КБ)")
    print(f"підпис: {len(caption)} символів, {caption.count(chr(10)) + 1} рядків")
    print("\n" + caption[:400] + ("…" if len(caption) > 400 else "") + "\n")

    if dry:
        print("[dry-run] нічого не опубліковано")
        return 0
    if not P.IG_TOKEN or not P.IG_USER_ID:
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID")
        return 1

    url = mf.upload_media(IMG, mf.token())
    print("медіа залито:", url)
    mid = publish_feed(url, caption)
    print(f"✔ Instagram {mid}")

    # Facebook не роняє запуск: інстаграмна публікація вже пройшла
    if not skip_fb:
        try:
            fb = publish_fb_feed(url, caption, P.page_token())
            print(f"✔ Facebook {fb}")
        except Exception as e:
            print(f"✖ Facebook не вийшло: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
