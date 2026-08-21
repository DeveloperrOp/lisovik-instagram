# -*- coding: utf-8 -*-
"""Единая конфигурация проекта. Без внешних зависимостей."""
import os
import re as _re
import sys
from pathlib import Path

try:  # Windows cp1252 падает на кириллице в выводе
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = PROJECT_ROOT / "content"
BRAND_DIR = PROJECT_ROOT / "brand"
OUT_DIR = PROJECT_ROOT / "out"
SAMPLES_DIR = PROJECT_ROOT / "samples"

# Доступы к Horoshop лежат в пайплайне карточек — не дублируем секреты
HOROSHOP_ENV = Path(
    r"D:\Клод код\Карточки для магазина\horoshop-card-pipeline"
    r"\horoshop-card-pipeline\.env"
)

# Хранилище медиа и очереди. Meta скачивает файл сама, поэтому объекты
# должны быть публично читаемыми.
GCS_BUCKET = os.environ.get("LISOVIK_BUCKET", "lisovik-ig-media")

# Instagram Graph API. Токен системного пользователя — бессрочный
# (проверено check_token.py: «спливає: ніколи»), обновлять по сроку не надо.
# В GitHub Actions приходит из секретов, локально — из окружения.
# Версию поднимаем осознанно: Meta гасит старые примерно за два года,
# а v26.0 — верхняя живая (v27 Graph уже не понимает).
IG_USER_ID = os.environ.get("IG_USER_ID", "")
IG_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
GRAPH_VERSION = "v26.0"

# Vertex AI
GCP_PROJECT = "project-b6733216-c1b5-4017-82e"
GCP_LOCATION = "global"
IMAGE_MODEL = "gemini-3.1-flash-image"   # 2K держит украинский текст без ошибок
IMAGE_MODEL_FALLBACK = "gemini-3-pro-image"
IMAGE_SIZE = "2K"                        # НЕ понижать: на 1K текст ломается

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# Товары, которые не идут в Instagram ни в каком виде
IG_BANNED_SUBSTRINGS = (
    "мухомор", "мухомора", "мухоморн", "аманіт", "amanita",
    "лотос", "lotus",          # психоактивное, серая зона Meta
)

# Категорий нет и не будет — не «временно распродано», а снято с продажи.
# Ловим и производные напитки: латте, какао и матча — это та же «Кава».
# По границе слова: «ціКАВИть» содержит «кави», «виКАВУють» и подобные тоже.
DISCONTINUED = (
    r"\bкав[аиуоі]\b", r"\bкавою\b", r"\bкавов", r"\bкаву\b",
    r"\bкакао\b", r"\bматч[ауі]\b", r"\bлате\b", r"\bлатте\b",
    r"\bкапучино\b", r"\bеспресо\b",
)

_DISCONTINUED = [_re.compile(p, _re.I) for p in DISCONTINUED]


def is_discontinued(text: str) -> bool:
    """Товар или тема сняты с продажи — не рекламируем даже намёком.

    Категория «Кава» распродана и не вернётся, а латте, какао и матча —
    это она же под другими названиями.
    """
    return any(p.search(text or "") for p in _DISCONTINUED)

# Названия товаров в каталоге содержат health claims («Для боротьби з тривожністю,
# апатією та депресією»). В Instagram такое публиковать нельзя — ни законом,
# ни правилами Meta. Здесь безопасная подача: артикул/ключ -> как называем в сторис.
SAFE_NAMES = {
    "zen mood": "Курс Zen Mood",
    "immunity guard": "Курс Immunity Guard",
    "heart power": "Курс Heart Power",
    "joint flex": "Курс Joint Flex",
    "harmony love": "Курс Harmony Love",
    "night balance": "Курс Night Balance",
    "focus flow": "Курс Focus Flow",
    "creativity unleashed": "Курс Creativity Unleashed",
    "детокс": "Курс Детокс",
    "man": "Курс MAN",
}

# Слова в НАЗВАНИИ товара, после которых название обязано пройти через SAFE_NAMES
CLAIM_MARKERS = (
    "тривожн", "депрес", "апаті", "імунітет", "судинн", "лікув", "хвороб",
    "безсон", "стрес", "суглоб", "гормон", "лібідо", "потенц", "паразит",
)


# Куски названий, которые вырезаем целиком
_CLAIM_PATTERNS = (
    _re.compile(r"\s*[:,]?\s*(анти|про)типаразитн\w*", _re.I),
    _re.compile(r"\s*для\s+(посилення|боротьби|покращення|зміцнення)[^,()]*", _re.I),
    _re.compile(r"\s*:\s*(для|курс)?[^:()]*"
                r"(тривожн|депрес|апаті|імунітет|судинн|безсон|суглоб|гормон|лібідо)"
                r"[^:()]*", _re.I),
)


def safe_display_name(name: str) -> str:
    """Название товара, пригодное для публикации в Instagram.

    Возвращает пустую строку, если безопасно назвать не удалось — такой товар
    в автопостинг не идёт.
    """
    low = (name or "").lower()
    for key, safe in SAFE_NAMES.items():
        if key in low:
            return safe

    out = name or ""
    for pat in _CLAIM_PATTERNS:
        out = pat.sub("", out)
    out = _re.sub(r"\s{2,}", " ", out).strip(" ,:-")

    return "" if has_claim(out) else out


def has_claim(text: str) -> bool:
    """Есть ли в тексте маркер медицинского обещания."""
    low = (text or "").lower()
    return any(m in low for m in CLAIM_MARKERS)


# Курсы и наборы — это миксы из нескольких банок, и на фото карточки видно
# всё, что в них входит. У «Курс Harmony Love» название чистое, состав в
# каталоге — просто «Мікс», а на фото средняя банка «МУХОМОР КОРОЛІВСЬКИЙ».
# Текстовые фильтры такое не ловят: запрещённое приходит картинкой.
# Поэтому в автопостинг миксы не идут вообще — только руками, глазами
# проверив фото.
MIX_CATEGORIES = ("курс", "набір", "набор", "мікс", "микс", "комплекс", "тріо", "трио")


def is_mix(name: str, category: str = "") -> bool:
    """Товар-микс: состав не виден из названия, на фото может быть что угодно."""
    low = f"{name} {category}".lower()
    return any(w in low for w in MIX_CATEGORIES)


def in_stock(presence: str) -> bool:
    """Товар реально в наличии.

    ОСТОРОЖНО: «Немає в наявності» содержит подстроку «наявн», поэтому
    проверка `"наявн" in presence` даёт ложное срабатывание на всём каталоге.
    """
    low = (presence or "").strip().lower()
    if not low:
        return False
    return not low.startswith("нема") and "наявності" in low


def load_env(path=None):
    """Простой парсер .env. Возвращает dict, ничего не печатает."""
    p = Path(path) if path else HOROSHOP_ENV
    data = {}
    if not p.exists():
        raise FileNotFoundError(f"Не найден .env: {p}")
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def is_ig_safe(name: str) -> bool:
    """Можно ли показывать товар в Instagram."""
    low = (name or "").lower()
    return not any(bad in low for bad in IG_BANNED_SUBSTRINGS)
