# -*- coding: utf-8 -*-
"""Рендер верстки в кадр: HTML/CSS → PNG 1080×1350.

Ярик 10.09 про мальовану PIL-версію: «дизайн так себе». Так і є: PIL
вміє покласти текст і залити прямокутник, а сітки, тіні, скло, тонкі
рамки й нормальні шрифти в ньому доводиться імітувати вручну.

Тому кадр верстається як сторінка й знімається браузером. Це дає все,
що є в макеті дизайнера: Google Fonts, backdrop-filter, градієнти,
SVG-іконки з рівною лінією, точні відступи.

    from render_html import shot
    shot(html, Path("out/x.png"))

Фон вставляється в HTML як data:URI, тому сторінка самодостатня й
рендериться без локального сервера.
"""
import base64
from pathlib import Path

W, H = 1080, 1350


def data_uri(path: Path) -> str:
    b = base64.b64encode(Path(path).read_bytes()).decode()
    ext = Path(path).suffix.lstrip(".").lower()
    return f"data:image/{'jpeg' if ext in ('jpg', 'jpeg') else ext};base64,{b}"


def shot(html: str, dest: Path, w=W, h=H, wait=1200) -> Path:
    from playwright.sync_api import sync_playwright
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": w, "height": h},
                         device_scale_factor=1)
        pg.set_content(html, wait_until="networkidle")
        # шрифти з мережі приїжджають після networkidle
        pg.wait_for_timeout(wait)
        pg.screenshot(path=str(dest))
        br.close()
    return dest
