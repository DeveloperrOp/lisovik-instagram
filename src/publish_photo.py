# -*- coding: utf-8 -*-
"""Публікація ОДНОГО фото в стрічку Instagram і Facebook.

Карусель публікує publish_carousel, сторіс — publish_one, а на
одинарний пост у стрічку скрипта не було: «Товар тижня» 06.09 виходив
руками. Тепер є.

    python publish_photo.py ../out/post_tyzhnia/пост.png
    python publish_photo.py ../out/post_tyzhnia/пост.png --dry-run

Підпис береться з caption.txt поруч із файлом або з однойменного .txt;
перевизначається прапорцем --caption.

Два обмеження Instagram, і обидва ловляться тією самою помилкою
«Only photo or video can be accepted as media type» (code 9004):
приймається лише JPEG, і в URL не має бути кирилиці. Тому файл
конвертується в JPEG під латинською назвою ще до заливки.
"""
import sys
from pathlib import Path

from PIL import Image

import manifest as mf
import publish as P
from config import OUT_DIR


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def publish_ig(url: str, caption: str) -> str:
    cid = P.api(f"{P.IG_USER_ID}/media",
                {"image_url": url, "caption": caption,
                 "access_token": P.IG_TOKEN}, "POST")["id"]
    r = P.api(f"{P.IG_USER_ID}/media_publish",
              {"creation_id": cid, "access_token": P.IG_TOKEN}, "POST")
    return r.get("id", "")


def publish_fb(url: str, caption: str, ptoken: str) -> str:
    r = P.api(f"{P.FB_PAGE_ID}/photos",
              {"url": url, "caption": caption, "access_token": ptoken}, "POST")
    return r.get("post_id") or r.get("id", "")


def main() -> int:
    P.load_dotenv()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("вкажи файл: python publish_photo.py <кадр.png>")
        return 1
    src = Path(args[0])
    if not src.exists():
        print("✖ немає файлу", src)
        return 1

    cap_file = arg("--caption")
    if not cap_file:
        for cand in (src.with_suffix(".txt"), src.parent / "caption.txt"):
            if cand.exists():
                cap_file = str(cand)
                break
    caption = (Path(cap_file).read_text(encoding="utf-8").strip()
               if cap_file and Path(cap_file).exists() else "")

    print(f"файл: {src.name} ({src.stat().st_size // 1024} КБ)")
    print(f"\nпідпис ({len(caption)} символів):\n{caption[:240]}"
          + ("…\n" if len(caption) > 240 else "\n"))
    if not caption:
        print("⚠ підпису немає — Instagram не дає його додати після публікації")

    if "--dry-run" in sys.argv:
        print("[dry-run] нічого не опубліковано")
        return 0
    if not P.IG_TOKEN or not P.IG_USER_ID:
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID")
        return 1

    tmp = OUT_DIR / "pending"
    tmp.mkdir(parents=True, exist_ok=True)
    dst = tmp / f"{src.parent.name}-post.jpg"
    Image.open(src).convert("RGB").save(dst, "JPEG", quality=92)

    tok = mf.token()
    url = mf.upload_media(dst, tok)
    print("залито у сховище:", url)

    print("✔ Instagram", publish_ig(url, caption))
    try:
        print("✔ Facebook", publish_fb(url, caption, P.page_token()))
    except Exception as e:
        print("✖ Facebook:", str(e)[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
