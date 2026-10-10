# -*- coding: utf-8 -*-
"""Публікація з локальної машини. ВИМКНЕНО 10.10.2026.

🚨 Не вмикай разом із ланцюгом на GitHub. Вони беруть кадр незалежно,
і коли збігаються в одну хвилину, той самий кадр іде у стрічку двічі:
09.10 о 18:02 і 10.10 о 10:00 так і сталось — два ig_media_id з різницею
в 30 секунд. git pull перед публікацією від цього не рятує, бо обидва
встигають прочитати чергу до того, як інший запише.

Друга причина: під Планувальником кожні 10 хвилин на екрані кліпало
чорне вікно — це дочірні git і python, яким pythonw не дає консолі.

Ланцюг на GitHub тримає добу сам (перевірено 09-10.10: ранковий кадр
о 07:00 вийшов обидва дні). Якщо колись знадобиться повернути цей
резерв — спершу зроби так, щоб два публікатори не могли взяти один
кадр: блокування через окремий файл у репозиторії або рознесення за
часом.

Навіщо. GitHub Actions виконує schedule як доведеться: заявлено кожні 15
хвилин, а фактичні розриви між запусками — від 91 до 1054 хвилин (замір
26-30.08.2026). Вузьке вікно він перестрибує, і кадр іде у failed. Це не
наша помилка конфігурації, а те, як безкоштовний планувальник працює.

Цей скрипт робить те саме, що workflow, але з машини власника, де
розклад виконується точно. Ставиться в Планувальник завдань Windows:

    schtasks /create /tn "lisovik-publish" /tr "..." /sc minute /mo 10

Обидва шляхи безпечні разом: маніфест спільний, а вже опубліковане
publish.py не чіпає.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
LOG = HERE.parent / "logs" / "publish_local.log"


def main() -> int:
    # git pull, щоб не публікувати за застарілою чергою: бот на GitHub
    # пише статуси у свій маніфест, і без підтягування вони розійдуться
    subprocess.run(["git", "pull", "--rebase", "-q", "origin", "master"],
                   cwd=HERE.parent, capture_output=True)
    r = subprocess.run([sys.executable, str(HERE / "publish.py")],
                       cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8")
    # Під pythonw консолі немає: sys.stdout може бути None, і звичайний
    # print роняє запуск іще до публікації. Тому пишемо в журнал — і
    # заодно видно, що відбувалось уночі, коли ніхто не дивився.
    out = (r.stdout or r.stderr or "").strip()
    stamp = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d %H:%M")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write("\n===== " + stamp + "\n" + out + "\n")
    try:
        print(out)
    except Exception:
        pass
    if "опубліковано:" in (r.stdout or ""):
        subprocess.run(["git", "add", "content/manifest.json"],
                       cwd=HERE.parent, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "queue: publish status"],
                       cwd=HERE.parent, capture_output=True)
        subprocess.run(["git", "push", "-q", "origin", "master"],
                       cwd=HERE.parent, capture_output=True)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
