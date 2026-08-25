# -*- coding: utf-8 -*-
"""Проверка, что мысль на кадре закончена, а не обрывок.

Требование Ярика: каждый кадр должен полностью раскрывать тему и давать
вывод. Один экран — одна законченная мысль, а не красивая фраза, после
которой непонятно, что делать.

Проверять это на глаз бесполезно: через месяц забудется. Поэтому здесь
формальные признаки незавершённости, которые ловятся машинно:

    claim → why → do

    claim  утверждение, конкретное
    why    почему так: механизм или причина
    do     что читателю сделать сегодня

    python check_thought.py content/thoughts.yaml
"""
import re
import sys
from pathlib import Path

import yaml

MAX = {"claim": 46, "why": 150, "do": 60}

# Обрыв: строка кончается служебным словом, за которым обязано идти
# продолжение. «Чага любить тепло, а не» — читатель ждёт остаток.
DANGLING = re.compile(
    r"\b(і|й|та|а|але|бо|що|щоб|як|коли|якщо|для|без|при|про|над|під|між|"
    r"через|перед|після|до|від|з|із|зі|на|у|в|о|об|по|за|не|ні|це|той|цей)\s*$",
    re.I)

# Действие: без глагола вывод не вывод, а ещё одно утверждение
ACTION = re.compile(
    r"\b(дай|додай|залий|настій|настоюй|проціди|бери|візьми|обери|почни|"
    r"тримай|пий|їж|змели|змішай|розмішай|запий|прибери|постав|перевір|"
    r"почекай|зачекай|лиши|залиш|роби|зроби|спробуй|клади|поклади|"
    r"зберігай|струсни|накрий|насип|вимкни|не\s+\w+)\b", re.I)

# То, чего в текстах про БАДы быть не может
CLAIMS = re.compile(
    r"\b(лік[уює]|зціл|виліков|терап|хворо|діагноз|симптом|імунітет|"
    r"депрес|тривож|безсон|тиск|цукор\s+у\s+крові|холестерин|запален|"
    r"детокс|очищ[уає]|виводить\s+токсин)", re.I)

DOSAGE = re.compile(r"\b\d+[\.,]?\d*\s?(г|мг|мл|грам|міліграм)\b", re.I)

# Пустые слова: занимают экран, не несут ничего
EMPTY = re.compile(
    r"\b(дар природи|сила лісу|натуральний продукт|унікальн|неймовірн|"
    r"справжн[яє] магія|секрет здоров|цілюща сила|чарівн)", re.I)


def check(t: dict) -> list:
    """Возвращает список претензий. Пусто — мысль закончена."""
    bad = []
    key = t.get("key", "?")

    for f in ("claim", "why", "do"):
        v = (t.get(f) or "").strip()
        if not v:
            bad.append(f"немає «{f}» — думка без нього не закінчена")
            continue
        if len(v) > MAX[f]:
            bad.append(f"{f}: {len(v)} символів, ліміт {MAX[f]}")
        if DANGLING.search(v):
            bad.append(f"{f} обривається на службовому слові: «{v[-28:]}»")

    do = (t.get("do") or "").strip()
    if do and not ACTION.search(do):
        bad.append(f"«do» не містить дії — це ще одне твердження, "
                   f"а не висновок: «{do[:40]}»")

    # why должно объяснять, а не повторять claim другими словами
    claim, why = (t.get("claim") or "").lower(), (t.get("why") or "").lower()
    if claim and why:
        cw = {w for w in re.findall(r"\w{5,}", claim)}
        ww = {w for w in re.findall(r"\w{5,}", why)}
        if cw and len(cw & ww) / len(cw) > 0.7:
            bad.append("«why» переказує «claim» тими самими словами, "
                       "а не пояснює причину")

    blob = " ".join(str(t.get(f, "")) for f in ("claim", "why", "do", "extra"))
    if CLAIMS.search(blob):
        bad.append(f"медична обіцянка: «{CLAIMS.search(blob).group(0)}»")
    if DOSAGE.search(blob):
        bad.append(f"дозування: «{DOSAGE.search(blob).group(0)}»")
    if EMPTY.search(blob):
        bad.append(f"порожні слова: «{EMPTY.search(blob).group(0)}»")

    # раскладки, которым нужны данные помимо трёх частей
    need = {"steps": 3, "versus": 2, "bullets": 3}
    lay = t.get("layout", "")
    if lay in need:
        parts = [p for p in (t.get("extra") or "").split("|") if p.strip()]
        if len(parts) < need[lay]:
            bad.append(f"розкладка «{lay}» потребує щонайменше "
                       f"{need[lay]} частин в extra, а їх {len(parts)}")
    if lay == "stat" and not re.search(r"\d", t.get("extra", "")):
        bad.append("розкладка «stat» без числа в extra")

    return bad


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "content/thoughts.yaml")
    if not path.exists():
        print(f"немає файлу {path}")
        return 1
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    thoughts = data["thoughts"] if isinstance(data, dict) else data

    bad_total = 0
    for t in thoughts:
        problems = check(t)
        if problems:
            bad_total += 1
            print(f"\n  ✖ {t.get('key', '?')} — {t.get('topic', '')}")
            for p in problems:
                print(f"      {p}")
    print(f"\nдумок: {len(thoughts)} | незакінчених: {bad_total}")
    if not bad_total:
        print("✅ кожна думка закінчена: є твердження, причина і дія")
    return 2 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
