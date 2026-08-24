# -*- coding: utf-8 -*-
"""Стилистический вайб недели: палитра, шрифты, свет.

Неделя берёт тему по кругу, поэтому лента не превращается в одну и ту же
картинку, повторённую сто раз. Структуру кадра тема не трогает — только
цвет, гарнитуру и тонировку.

    import theme
    t = theme.for_week(2)      # тема второй недели
    theme.apply(t)             # включить её в layouts

Проверка «шрифт есть в системе» тут обязательна: если гарнитуры нет,
PIL падает уже в момент отрисовки, посреди пачки кадров.
"""
from pathlib import Path

import yaml

from config import CONTENT_DIR

THEMES = CONTENT_DIR / "themes.yaml"
FONT_DIR = Path("C:/Windows/Fonts")

_cache = None


def all_themes() -> list:
    global _cache
    if _cache is None:
        _cache = yaml.safe_load(THEMES.read_text(encoding="utf-8"))["themes"]
    return _cache


def font_path(name: str) -> str:
    p = FONT_DIR / f"{name}.ttf"
    if not p.exists():
        raise FileNotFoundError(
            f"немає шрифту {name}.ttf — тема на нього посилається, "
            f"але в системі його не встановлено")
    return str(p)


def for_week(week: int) -> dict:
    """Тема недели по кругу: неделя 1 — первая, неделя 6 — снова первая."""
    t = all_themes()
    return t[(int(week) - 1) % len(t)]


def by_key(key: str) -> dict:
    for t in all_themes():
        if t["key"] == key:
            return t
    raise KeyError(f"немає теми {key!r}; є: "
                   + ", ".join(x["key"] for x in all_themes()))


def apply(t: dict) -> None:
    """Включает тему в layouts.

    Модуль настраивается подменой его констант — так правится четыре строки
    вместо шестидесяти обращений к цвету и шрифту по всему файлу. Рендер
    однопоточный и последовательный, так что глобальное состояние тут
    безопасно; тема ставится один раз перед пачкой кадров.
    """
    import layouts as L

    L.FONT_BOLD = font_path(t["fonts"]["bold"])
    L.FONT_SEMI = font_path(t["fonts"]["semi"])
    L.FONT_REG = font_path(t["fonts"]["reg"])
    L.CREAM = tuple(t["cream"])
    L.DIM = tuple(t["dim"])
    L.MOSS = tuple(t["accent"])
    L.INK = tuple(t["ink"])
    L.TINT = tuple(t["tint"])
    L.PANEL = tuple(t.get("panel", t["tint"]))
    L.VEIL_SHIFT = int(t.get("veil", 0))
