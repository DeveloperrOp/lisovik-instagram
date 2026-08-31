# -*- coding: utf-8 -*-
"""Публікація з локальної машини — резерв замість розкладу GitHub.

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
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    # git pull, щоб не публікувати за застарілою чергою: бот на GitHub
    # пише статуси у свій маніфест, і без підтягування вони розійдуться
    subprocess.run(["git", "pull", "--rebase", "-q", "origin", "master"],
                   cwd=HERE.parent, capture_output=True)
    r = subprocess.run([sys.executable, str(HERE / "publish.py")],
                       cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8")
    print(r.stdout or r.stderr)
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
