# -*- coding: utf-8 -*-
"""Публікація Reels в Instagram і того самого відео на сторінку Facebook.

    python publish_reel.py <файл.mp4> --caption <файл.txt> --dry-run
    python publish_reel.py ../out/reels/yasna.mp4 --caption ../out/reels/yasna.txt

Вимоги Meta до Reels, об які легко спіткнутись:
  · відео ТІЛЬКИ H.264 + AAC. HEVC (H.265) дає помилку 9004
    «Only photo or video can be accepted as media type» — ту саму, що й
    непідтримуваний формат картинки, тож за текстом не здогадаєшся;
  · адреса файлу має бути латиницею: кирилиця в імені перетворюється на
    посилання, яке Meta не завантажує, і помилка знову та сама 9004;
  · 9:16, до 1080 по ширині, 23-60 кадрів/с, до 15 хвилин, до 1 ГБ.

Відео обробляється довше за картинку, тому чекаємо окремим циклом із
довшим терпінням, ніж у publish.wait_ready.
"""
import subprocess
import sys
import time
from pathlib import Path

import manifest as mf
import publish as P

POLL_TRIES = 90          # відео готується довше за фото
POLL_SLEEP = 6


def probe(path: Path) -> dict:
    """Параметри відео. Без ffprobe просто не перевіряємо — не падаємо."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size", "-show_entries",
             "stream=codec_name,codec_type,width,height",
             "-of", "default=noprint_wrappers=1", str(path)],
            capture_output=True, text=True, timeout=60)
    except Exception:
        return {}
    out = {}
    for line in (r.stdout or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out.setdefault(k, []).append(v)
    return out


def complain(info: dict) -> list:
    """Що Meta не пропустить. Порожній список — можна лити."""
    bad = []
    codecs = info.get("codec_name", [])
    if codecs and "h264" not in codecs:
        bad.append(f"відео не H.264, а {codecs[0]} — Meta не прийме")
    if codecs and "aac" not in codecs:
        bad.append("немає доріжки AAC")
    w = int(info.get("width", [0])[0] or 0)
    h = int(info.get("height", [0])[0] or 0)
    if w and w > 1080:
        bad.append(f"ширина {w}px, а треба не більше 1080")
    if w and h and abs(w / h - 9 / 16) > 0.02:
        bad.append(f"співвідношення {w}:{h}, а Reels хоче 9:16")
    dur = float(info.get("duration", [0])[0] or 0)
    if dur and dur > 900:
        bad.append(f"довжина {dur:.0f} с, ліміт 15 хвилин")
    size = int(info.get("size", [0])[0] or 0)
    if size > 1_000_000_000:
        bad.append("файл більший за 1 ГБ")
    return bad


def wait_video(cid: str) -> bool:
    for n in range(POLL_TRIES):
        r = P.api(cid, {"fields": "status_code,status",
                        "access_token": P.IG_TOKEN})
        code = r.get("status_code")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            raise RuntimeError(f"Meta не обробила відео: {r.get('status')}")
        if n % 5 == 0:
            print(f"    · обробка… {n * POLL_SLEEP} с", flush=True)
        time.sleep(POLL_SLEEP)
    raise RuntimeError("відео не обробилось за відведений час")


def publish_ig_reel(url: str, caption: str) -> str:
    cid = P.api(f"{P.IG_USER_ID}/media",
                {"media_type": "REELS", "video_url": url,
                 "caption": caption, "share_to_feed": "true",
                 "access_token": P.IG_TOKEN}, "POST")["id"]
    print("  контейнер:", cid, flush=True)
    wait_video(cid)
    return P.api(f"{P.IG_USER_ID}/media_publish",
                 {"creation_id": cid, "access_token": P.IG_TOKEN},
                 "POST")["id"]


def publish_fb_video(url: str, caption: str, ptoken: str) -> str:
    r = P.api(f"{P.FB_PAGE_ID}/videos",
              {"file_url": url, "description": caption,
               "access_token": ptoken}, "POST")
    return r.get("id", "")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main() -> int:
    P.load_dotenv()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("вкажи файл: python publish_reel.py <відео.mp4>")
        return 1
    video = Path(args[0])
    if not video.exists():
        print("✖ немає файлу", video)
        return 1

    cap_file = arg("--caption")
    caption = (Path(cap_file).read_text(encoding="utf-8").strip()
               if cap_file and Path(cap_file).exists() else "")

    info = probe(video)
    print(f"файл: {video.name} ({video.stat().st_size // 1024 // 1024} МБ)")
    if info:
        print(f"  {info.get('width',['?'])[0]}×{info.get('height',['?'])[0]}, "
              f"{float(info.get('duration',[0])[0] or 0):.0f} с, "
              f"{', '.join(info.get('codec_name', []))}")
    bad = complain(info)
    for b in bad:
        print("  ✖", b)
    if bad:
        print("\nвідео треба перекодувати, публікація скасована")
        return 1
    if not video.stem.isascii():
        print("  ✖ ім'я файлу не латиницею — Meta не завантажить посилання")
        return 1

    print(f"\nпідпис ({len(caption)} символів):\n{caption[:300]}\n")
    if "--dry-run" in sys.argv:
        print("[dry-run] нічого не опубліковано")
        return 0
    if not P.IG_TOKEN or not P.IG_USER_ID:
        print("✖ немає IG_ACCESS_TOKEN / IG_USER_ID")
        return 1

    url = mf.upload_media(video, mf.token())
    print("залито у сховище:", url, flush=True)

    mid = publish_ig_reel(url, caption)
    print(f"✔ Instagram Reels {mid}")

    if "--no-fb" not in sys.argv:
        try:
            print(f"✔ Facebook {publish_fb_video(url, caption, P.page_token())}")
        except Exception as e:
            print(f"✖ Facebook не вийшло: {str(e)[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
