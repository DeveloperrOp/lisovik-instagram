# -*- coding: utf-8 -*-
"""Ревью сторіс у Telegram: дивишся кадр з телефона і вирішуєш його долю.

    python review_bot.py send     # надіслати те, що чекає на ревʼю
    python review_bot.py listen   # слухати натискання кнопок
    python review_bot.py queue    # що зараз у черзі

Кнопка «В ефір» одразу заливає кадр у GCS і ставить його в чергу публікації —
щоб опублікувати, компʼютер уже не потрібен.

Перший місяць дивимось кожен кадр очима: модель уміє домалювати мухомор
або перекрутити текст, і жоден лінтер цього не побачить.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import yaml

import manifest as mf
from config import CONTENT_DIR, OUT_DIR

TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TG_TOKEN}"

PENDING = OUT_DIR / "pending"
PLAN = CONTENT_DIR / "content_plan.yaml"
STATE = OUT_DIR / "review_state.json"

CHECKLIST = (
    "Перевір перед «В ефір»:\n"
    "• текст без помилок, без латиниці й без дублів рядків\n"
    "• у кадрі немає мухомора (червона шапка в горошок)\n"
    "• на банках і пачках немає вигаданих етикеток і чужих брендів\n"
    "• немає обіцянок лікування\n"
    "• дисклеймер читається"
)


def tg(method: str, params: dict = None, files: dict = None) -> dict:
    """Виклик Telegram API. Без залежностей — тільки stdlib."""
    params = params or {}
    if files:
        boundary = "----lisovik"
        body = b""
        for k, v in params.items():
            body += (f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{k}"\r\n\r\n{v}\r\n').encode("utf-8")
        for k, (fname, data) in files.items():
            body += (f"--{boundary}\r\nContent-Disposition: form-data; "
                     f'name="{k}"; filename="{fname}"\r\n'
                     f"Content-Type: application/octet-stream\r\n\r\n").encode("utf-8")
            body += data + b"\r\n"
        body += f"--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(
            f"{API}/{method}", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        req = urllib.request.Request(
            f"{API}/{method}",
            data=urllib.parse.urlencode(params).encode("utf-8"))
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8", "replace")[:300]}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"sent": {}, "offset": 0}


def save_state(state: dict):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                     encoding="utf-8")


def plan_index() -> dict:
    plan = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    return {s["id"]: s for s in plan["stories"]}, plan["defaults"]


def keyboard(sid: str) -> str:
    return json.dumps({"inline_keyboard": [[
        {"text": "✅ В ефір", "callback_data": f"ok:{sid}"},
        {"text": "🔄 Переробити", "callback_data": f"redo:{sid}"},
        {"text": "🗑 Видалити", "callback_data": f"del:{sid}"},
    ]]})


def cmd_send(limit=10):
    """Надсилає кадри, які ще не бачив Ярик."""
    stories, _ = plan_index()
    state = load_state()
    sent = 0

    for path in sorted(PENDING.glob("*.jpg")):
        sid = path.stem
        if sid in state["sent"] or sid not in stories:
            continue
        s = stories[sid]
        caption = (f"<b>{s['headline']}</b>\n{s.get('subline','')}\n\n"
                   f"{s['rubric']} · тиждень {s['week']} · {s['day']} {s['slot']}\n"
                   f"<i>{s['mode']}</i>")
        r = tg("sendPhoto",
               {"chat_id": TG_CHAT, "caption": caption, "parse_mode": "HTML",
                "reply_markup": keyboard(sid)},
               {"photo": (path.name, path.read_bytes())})
        if r.get("ok"):
            state["sent"][sid] = r["result"]["message_id"]
            sent += 1
            print(f"  → {sid}")
        else:
            print(f"  ✖ {sid}: {r.get('error') or r}")
        if sent >= limit:
            break

    save_state(state)
    if sent:
        tg("sendMessage", {"chat_id": TG_CHAT, "text": CHECKLIST})
    print(f"надіслано: {sent}")


def slot_datetime(story: dict, defaults: dict, week_start: datetime) -> tuple:
    """Коли саме публікувати цей кадр."""
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    offset = (story["week"] - 1) * 7 + days.index(story["day"])
    date = week_start + timedelta(days=offset)
    return mf.slot_window(date, defaults["slots"][story["slot"]])


def approve(sid: str, stories: dict, defaults: dict, week_start: datetime):
    """Кладе кадр у GCS і ставить у чергу публікації."""
    path = PENDING / f"{sid}.jpg"
    if not path.exists():
        return f"немає файлу {sid}.jpg"
    tok = mf.token()
    url = mf.upload_media(path, tok)
    start, end = slot_datetime(stories[sid], defaults, week_start)
    m = mf.load(tok)
    mf.add(m, stories[sid], url, start.isoformat(), end.isoformat(),
           status="approved")
    mf.save(m, tok)
    return f"у черзі на {start:%d.%m %H:%M}"


def cmd_listen(week_start: datetime):
    """Слухає натискання кнопок. Для постійної роботи — Cloud Run + webhook."""
    stories, defaults = plan_index()
    state = load_state()
    print("слухаю кнопки, Ctrl+C щоб зупинити")

    while True:
        r = tg("getUpdates", {"offset": state["offset"] + 1, "timeout": 50})
        if not r.get("ok"):
            print("помилка:", r.get("error") or r)
            break
        for upd in r["result"]:
            state["offset"] = upd["update_id"]
            cq = upd.get("callback_query")
            if not cq:
                continue
            action, _, sid = cq["data"].partition(":")
            if action == "ok":
                msg = approve(sid, stories, defaults, week_start)
                answer = f"✅ {sid}: {msg}"
            elif action == "redo":
                (PENDING / f"{sid}_bg.png").unlink(missing_ok=True)
                (PENDING / f"{sid}.jpg").unlink(missing_ok=True)
                state["sent"].pop(sid, None)
                answer = f"🔄 {sid}: перегенерувати"
            else:
                (PENDING / f"{sid}_bg.png").unlink(missing_ok=True)
                (PENDING / f"{sid}.jpg").unlink(missing_ok=True)
                answer = f"🗑 {sid}: видалено"

            tg("answerCallbackQuery",
               {"callback_query_id": cq["id"], "text": answer[:190]})
            tg("editMessageCaption",
               {"chat_id": TG_CHAT, "message_id": cq["message"]["message_id"],
                "caption": answer, "parse_mode": "HTML"})
            print(" ", answer)
            save_state(state)


def cmd_queue():
    m = mf.load()
    s = mf.stats(m)
    print(f"у черзі: {len(m['items'])}")
    for k, v in s.items():
        if v:
            print(f"  {k}: {v}")


def main():
    if not TG_TOKEN or not TG_CHAT:
        print("✖ немає TG_BOT_TOKEN / TG_CHAT_ID в оточенні")
        print("  токен береться у @BotFather, chat_id — у @userinfobot")
        return 1

    cmd = sys.argv[1] if len(sys.argv) > 1 else "queue"
    # понеділок поточного тижня як точка відліку розкладу
    today = datetime.now(mf.KYIV).replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())

    if cmd == "send":
        cmd_send()
    elif cmd == "listen":
        cmd_listen(week_start)
    else:
        cmd_queue()
    return 0


if __name__ == "__main__":
    sys.exit(main())
