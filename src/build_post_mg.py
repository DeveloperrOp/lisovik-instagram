# -*- coding: utf-8 -*-
"""Карусель у стрічку: магній гліцинат, вісім кадрів.

Синій вайб обрав Ярик 29.09 з трьох проб. Перша збірка була «дуже просто
і постно» — половина кадрів суцільна заливка з абзацом, фото каталожні,
банка по центру порожнього тла. Тому тут три правила:

  · сцена замість вітрини — кава й стіл, вечірня лампа, склянка води,
    рука з капсулою. Картка сама називає, куди дівається магній:
    «стрес, кава, спорт, спека»;
  · графіка замість абзацу — перекреслене число, смуга «208 із 375»,
    шкала переносимості форм, схема хелата;
  · жодного кадру без фактури.

Кадри з рукою й капсулами малюються БЕЗ референсу банки: поки фото
прикріплене, модель ставить у кадр банки, хоч як проси навпаки, і вони
лізуть під текст.

Правило власника: ПРОДУКТ НА ПЕРШОМУ КАДРІ.

  1 обкладинка  ранковий стіл, кава, банка — 104 мг і ціна дня
  2 аргумент    перекреслені 600 мг проти 104, рука з капсулою
  3 цифра       смуга «208 із 375», склянка води
  4 форми       шкала оксид / цитрат / бісгліцинат
  5 хелат       схема «гліцин + Mg + гліцин», макро капсули
  6 схема       вечір, лампа: одна вранці, одна ввечері
  7 офіційно    дозволені формулювання, кадр після навантаження
  8 фінал       дві фасовки й ціни

Дозування тут дозволені: заборона на них — правило сторіс, а весь сенс
цього поста саме в цифрі.

    python build_post_mg.py            # згенерувати й зібрати
    python build_post_mg.py --compose  # тільки перезібрати з наявних фонів
"""
import sys
from pathlib import Path

from PIL import Image

import build_day as B
import fullgen as F
import generate as gen
from config import OUT_DIR
from render_html import shot, data_uri

OUT = OUT_DIR / "post_mg"
REFS = [OUT_DIR / "real" / "all" / "magnium.jpg"]
W, H = 1080, 1350

KEEP = (" The bottle keeps its own printed label exactly as in the attached "
        "photo: WHITE opaque plastic with a WHITE lid and a DEEP NAVY BLUE "
        "paper band around the middle carrying the white ЛІСОВИК tree-face "
        "logo and, under it, the two lines ДІЄТИЧНА ДОБАВКА and МАГНІЙ "
        "ГЛІЦИНАТ spelled letter for letter. The lid, neck, shoulders and "
        "bottom rim stay plain white. There is EXACTLY ONE bottle in the "
        "frame.")
# Модель любить дописати на капсулі штамп на кшталт «N50» — це вигадане
# маркування чужого виробника, і в кадрі йому не місце.
BLANK = (" Any capsules in the frame are plain and blank: no letters, no "
         "numbers, no markings printed on them.")
TAIL = (" NO TEXT anywhere in the image except the wording printed on the "
        "product label. No stamps, seals or badges in the background." + BLANK)

# Сцени без банки: малюються draw_raw, інакше референс тягне банки в кадр.
NOREF = {"k2", "k3", "k4", "k5", "k7"}

SCENES = {
 "k1": (
    "Editorial lifestyle photograph, moody blue-toned morning light falling "
    "from a window on the left across a dark wooden desk: a cup of black "
    "coffee, an open notebook and the bottle from the attached photo stand "
    "together in the LOWER RIGHT of the frame, shot slightly from above at a "
    "human angle, shallow depth of field, the background falling into deep "
    "blue shadow. The UPPER HALF of the frame is dark blue shadow and empty."
    + KEEP + TAIL),
 "k2": (
    "Close-up editorial photograph, deep navy blue tones, one hard light from "
    "the left: a hand holds a single pale ivory capsule between thumb and "
    "forefinger, entirely inside the BOTTOM THIRD of the frame, the wrist "
    "entering from the bottom right corner, sharp and detailed, skin natural, "
    "nails bare and short. There is NO bottle, NO jar and NO packaging "
    "anywhere in this image. The TOP TWO THIRDS of the frame are plain dark "
    "blue with nothing in them at all. The hand is anatomically correct with "
    "exactly five fingers." + TAIL),
 "k3": (
    "Editorial lifestyle photograph, deep navy blue tones, soft side light: a "
    "plain glass of water stands on a dark wooden table in the LOWER RIGHT of "
    "the frame with two pale ivory capsules lying beside it, shallow depth of "
    "field, the background falling into dark blue. There is NO bottle, NO jar "
    "and NO packaging anywhere in this image. The TOP TWO THIRDS of the frame "
    "are dark blue and empty." + TAIL),
 "k4": (
    "Extreme macro photograph on a dark navy blue surface, one hard raking "
    "light from the left, deep shadows: a loose scattering of pale ivory "
    "capsules fills the BOTTOM QUARTER of the frame, razor sharp, every "
    "detail visible. There is NO bottle, NO jar and NO packaging anywhere in "
    "this image. The TOP THREE QUARTERS of the frame are plain dark navy "
    "blue, nothing in them at all." + TAIL),
 "k5": (
    "Extreme macro photograph, deep navy blue tones, one soft light: a SINGLE "
    "pale ivory capsule lies alone on a dark navy surface, small and centred "
    "inside the BOTTOM QUARTER of the frame, razor sharp, with a gentle "
    "reflection under it. There is NO bottle, NO jar and NO packaging "
    "anywhere in this image. The TOP THREE QUARTERS of the frame are plain "
    "dark navy blue, nothing in them at all." + TAIL),
 "k6": (
    "Editorial lifestyle photograph, warm bedside lamp glowing on the right "
    "against deep blue night tones: a glass of water and the bottle from the "
    "attached photo stand on a dark wooden bedside table in the LOWER LEFT of "
    "the frame, a rumpled bed blurred behind, shot at a human angle. The "
    "UPPER HALF of the frame is dark blue and almost empty." + KEEP + TAIL),
 "k7": (
    "Editorial lifestyle photograph, deep navy blue tones, one cool side "
    "light: a plain unbranded stainless steel water bottle and a folded grey "
    "towel lie on a dark wooden bench after training, together and SMALL "
    "inside the BOTTOM FIFTH of the frame — nothing reaches above that "
    "line — shallow depth of field, the room "
    "behind blurred into dark blue. There is NO supplement bottle, NO jar, NO "
    "packaging and NO people anywhere in this image. ABSOLUTELY NO TEXT, NO "
    "letters, NO numbers, NO logos and NO brand names anywhere in this image "
    "— the bottle and the towel are completely blank. The TOP FOUR FIFTHS "
    "of the frame are dark blue and empty."),
 "k8": (
    "Editorial lifestyle photograph, cool blue evening light across a dark "
    "wooden table: the bottle from the attached photo stands in the LOWER "
    "RIGHT of the frame beside a plain glass of water, seen slightly from the "
    "side at a human angle, one long soft shadow to the left, the background "
    "falling into deep blue. The UPPER HALF of the frame is dark blue and "
    "empty." + KEEP + TAIL),
}

FONTS = ("<link rel='preconnect' href='https://fonts.gstatic.com'>"
         "<link href='https://fonts.googleapis.com/css2?family=Montserrat:"
         "wght@400;500;600;700;800;900&display=swap' rel='stylesheet'>")

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden;position:relative;
 font-family:Montserrat;color:#eef3fb;-webkit-font-smoothing:antialiased}
.bg{position:absolute;inset:0;background:url('@BG@') center/cover}
.wash{position:absolute;inset:0;background:linear-gradient(180deg,
 rgba(9,20,42,.9) 0%,rgba(9,20,42,.64) 34%,rgba(9,20,42,0) 56%)}
.col{position:absolute;left:8%;right:8%;top:6%}
.eye{font-weight:700;font-size:24px;letter-spacing:.3em;text-transform:uppercase;
 color:#8fb3e0;margin-bottom:22px}
h1{font-weight:800;font-size:@H1@px;line-height:.96;letter-spacing:-2px;
 text-transform:uppercase}
p{font-weight:500;font-size:@P@px;line-height:1.36;margin-top:22px;
 max-width:84%;color:rgba(238,243,251,.88)}

.crossed{display:inline-block;position:relative;font-weight:900;font-size:150px;
 line-height:1;letter-spacing:-6px;color:rgba(238,243,251,.4)}
.crossed:after{content:'';position:absolute;left:-10px;right:-10px;top:52%;
 height:9px;background:#ff6b4a;transform:rotate(-7deg)}
.win{font-weight:900;font-size:190px;line-height:.9;letter-spacing:-9px;
 color:#fff;margin-top:6px}
.win i{font-style:normal;font-weight:800;font-size:56px;letter-spacing:0;
 margin-left:10px}

.meter{margin-top:34px}
.meter .track{height:34px;background:rgba(143,179,224,.22);border-radius:17px;
 overflow:hidden}
.meter .track span{display:block;height:100%;width:55%;border-radius:17px;
 background:linear-gradient(90deg,#7fd4a3,#9fc4f0)}
.meter .legend{display:flex;justify-content:space-between;margin-top:14px;
 font-weight:700;font-size:27px;color:#9fc4f0}
.meter .legend b{color:#fff;font-weight:800}

.bars{margin-top:32px}
.row{display:flex;align-items:center;gap:18px;margin-bottom:20px}
.name{width:250px;font-weight:800;font-size:31px;text-transform:uppercase}
.bar{flex:1;height:22px;background:rgba(143,179,224,.22);border-radius:11px;
 overflow:hidden}
.bar span{display:block;height:100%;border-radius:11px}
.note{font-weight:600;font-size:26px;color:#9fc4f0;width:200px;text-align:right}

.chel{display:flex;align-items:center;gap:18px;margin-top:36px}
.atom{width:168px;height:168px;border-radius:50%;display:flex;
 align-items:center;justify-content:center;font-weight:800;font-size:29px;
 text-align:center;line-height:1.1}
.atom.mg{background:#9fc4f0;color:#12244a;font-size:38px}
.atom.gl{background:rgba(143,179,224,.2);border:2px solid rgba(143,179,224,.5);
 color:#dce7f7}
.plus{font-weight:800;font-size:46px;color:#8fb3e0}

.when{margin-top:34px}
.when div{display:flex;align-items:baseline;gap:20px;padding:22px 0;
 border-bottom:1px solid rgba(143,179,224,.3)}
.when b{font-weight:800;font-size:34px;color:#fff;width:190px;
 text-transform:uppercase}
.when span{font-weight:600;font-size:31px;color:#dce7f7}

ul{list-style:none;margin-top:28px}
li{font-weight:600;font-size:32px;line-height:1.28;padding:18px 0;
 border-bottom:1px solid rgba(143,179,224,.3);color:#dce7f7}
.do{position:absolute;left:8%;bottom:6%;font-weight:800;font-size:30px;
 letter-spacing:.06em;text-transform:uppercase;color:#12244a;
 background:#9fc4f0;padding:18px 26px;border-radius:4px}
.pg{position:absolute;right:8%;bottom:7.5%;font-weight:700;font-size:26px;
 letter-spacing:.2em;color:#7ea3d6}
"""

BARS = [("Оксид", 26, "#ff6b4a", "важкий для шлунка"),
        ("Цитрат", 55, "#ffb347", "послаблює"),
        ("Бісгліцинат", 96, "#7fd4a3", "найм'якший")]

CARDS = [
 dict(key="k1", eye="Магній гліцинат", h1="104 мг, а не вага солі",
      p="На банках пишуть вагу сполуки. Рахувати ж треба елементарний "
        "магній — той, що справді дійде до тебе.",
      do="від 16 грн на день", h1size=88, psize=32),
 dict(key="k2", eye="Як читають банку", kind="crossed",
      p="Велика цифра на банці — це вага всієї сполуки. Магнію в ній лише "
        "частина. Ми пишемо той, що рахують.", h1size=88, psize=32),
 dict(key="k3", eye="Скільки насправді", h1="208 мг із 375", kind="meter",
      p="Дві капсули закривають більше половини добової норми. Решту "
        "спокійно добирає їжа.", h1size=92, psize=32),
 dict(key="k4", eye="Три форми магнію", h1="Чому бісгліцинат", kind="bars",
      p="До третьої форми приходять тоді, коли перші дві не підійшли.",
      h1size=92, psize=31),
 dict(key="k5", eye="Що таке хелат", h1="Мінерал у гліциновій обгортці",
      kind="chel",
      p="Друга половина сполуки — амінокислота гліцин. Саме через неї форму "
        "традиційно ставлять у вечірній прийом.", h1size=76, psize=31),
 dict(key="k6", eye="Схема", h1="Одна вранці, одна ввечері", kind="when",
      p="Капсули однакові, рахувати нічого не треба.", h1size=84, psize=31),
 dict(key="k7", eye="Офіційно", h1="Це не наші слова",
      items=["зменшення втоми та виснаження",
             "нормальна робота нервової системи",
             "нормальна робота м'язів",
             "нормальний психологічний стан"],
      p="Формулювання з європейського реєстру. Право на них дає вміст від "
        "15% норми — у нас 55%.", h1size=92, psize=29),
 dict(key="k8", eye="Дві фасовки", h1="60 або 120 капсул",
      p="590 грн на місяць, 985 на два — від 16 грн на день. Оболонка "
        "капсули рослинна, без желатину.",
      do="Посилання в шапці профілю", h1size=92, psize=32),
]


def graphic(kind: str) -> str:
    """Блок, який замінює абзац: число, смуга, шкала, схема чи розклад."""
    if kind == "crossed":
        return ("<div class='crossed'>600 мг</div>"
                "<div class='win'>104<i>мг</i></div>")
    if kind == "meter":
        return ("<div class='meter'><div class='track'><span></span></div>"
                "<div class='legend'><b>208 мг на добу</b>"
                "<span>норма 375 мг</span></div></div>")
    if kind == "bars":
        return "<div class='bars'>" + "".join(
            "<div class='row'><div class='name'>" + n + "</div>"
            "<div class='bar'><span style='width:" + str(w) + "%;background:" +
            c + "'></span></div><div class='note'>" + note + "</div></div>"
            for n, w, c, note in BARS) + "</div>"
    if kind == "chel":
        return ("<div class='chel'><div class='atom gl'>гліцин</div>"
                "<div class='plus'>+</div><div class='atom mg'>Mg</div>"
                "<div class='plus'>+</div><div class='atom gl'>гліцин</div>"
                "</div>")
    if kind == "when":
        return ("<div class='when'>"
                "<div><b>Вранці</b><span>одна капсула, запиваючи водою</span>"
                "</div><div><b>Увечері</b><span>одна капсула, ближче до сну"
                "</span></div></div>")
    return ""


def esc(s):
    return (s or "").replace("&", "&amp;")


def render(c: dict, bg: Path, n: int) -> str:
    css = (CSS.replace("@H1@", str(c["h1size"]))
              .replace("@P@", str(c["psize"]))
              .replace("@BG@", data_uri(bg)))
    head = "" if c.get("kind") == "crossed" else "<h1>" + esc(c["h1"]) + "</h1>"
    rows = ("<ul>" + "".join("<li>" + esc(x) + "</li>" for x in c["items"]) +
            "</ul>" if c.get("items") else "")
    body = ("<div class='col'><div class='eye'>" + esc(c["eye"]) + "</div>" +
            head + graphic(c.get("kind", "")) + rows +
            "<p>" + esc(c["p"]) + "</p></div>")
    do = "<div class='do'>" + esc(c["do"]) + "</div>" if c.get("do") else ""
    return ("<html><head>" + FONTS + "<style>" + css + "</style></head><body>"
            "<div class='bg'></div><div class='wash'></div>" + body + do +
            "<div class='pg'>" + str(n) + " / " + str(len(CARDS)) +
            "</div></body></html>")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_blank").mkdir(exist_ok=True)
    tok = None if "--compose" in sys.argv else gen.token()

    for n, c in enumerate(CARDS, 1):
        key = c["key"]
        bg = OUT / f"bg_{key}.png"
        if not bg.exists() and tok:
            scene = SCENES[key]
            if key in NOREF:
                ok = F.draw_raw(scene, tok, bg, aspect="4:5")
            else:
                ok = F.draw_ref(scene + " " + " ".join(B.REF_MANY.split()),
                                REFS, tok, bg, aspect="4:5")
            print(("  ✔ фон " if ok else "  ✖ фон ") + key, flush=True)
        if not bg.exists():
            print("  ✖ немає фону", key)
            continue
        html = render(c, bg, n)
        png = OUT / f"{n}_{key}.png"
        shot(html, png, w=W, h=H)
        shot(html.replace("</style>",
                          ".col,.col *,.do,.pg{color:transparent!important}"
                          "</style>"),
             OUT / "_blank" / f"{n}_{key}.png", w=W, h=H)
        Image.open(png).convert("RGB").save(
            OUT / f"{n}_{key}.jpg", "JPEG", quality=92)
        print("  ✔ кадр", n, key, flush=True)

    print("тека:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
