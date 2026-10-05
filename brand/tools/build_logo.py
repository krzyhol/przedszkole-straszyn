#!/usr/bin/env python3
"""
Generator zestawu logo Przedszkola św. Jacka w Straszynie.

Wszystkie pliki SVG w brand/logo/svg powstają z tego skryptu — tekst jest
zamieniony na krzywe, więc logo wygląda identycznie bez instalowania fontów.

Wymagania:  pip install fonttools uharfbuzz
Fonty (licencja OFL, Google Fonts) pobierane są automatycznie do brand/tools/fonts:
  Baloo 2 (napisy główne), Nunito Sans (napisy pomocnicze)

Użycie:     python3 brand/tools/build_logo.py
PNG:        node brand/tools/export_png.mjs   (wymaga: npm i @resvg/resvg-js)
"""
import io
import os
import urllib.request

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "logo", "svg"))
FONT_DIR = os.path.join(HERE, "fonts")
FONT_URLS = {
    "Baloo2.ttf": "https://github.com/google/fonts/raw/main/ofl/baloo2/Baloo2%5Bwght%5D.ttf",
    "NunitoSans.ttf": "https://github.com/google/fonts/raw/main/ofl/nunitosans/NunitoSans%5BYTLC,opsz,wdth,wght%5D.ttf",
}

# ---------------------------------------------------------------- kolory marki
C = {
    "leaf": "#356a45",     # zieleń przewodnia (łuk, napisy)
    "leaf_d": "#274e34",
    "grass": "#7bbf6f",    # wzgórze
    "sun": "#f4b13c",      # słońce
    "sun_d": "#8a520c",    # buzia słońca
    "cheek": "#f08a5d",
    "cream": "#fffaf0",    # wieża
    "paper": "#fbf8f1",
    "ink": "#23332a",
    "ink_soft": "#4d5e53",
    "red": "#d24a39",      # Biedronki
    "blue": "#3f7dae",     # Motylki
    "blue_l": "#6ea6d6",
    "amber": "#e0a02b",    # Pszczółki
    "bug_d": "#2a1512",
    "wing": "#cfe5f5",
    "mint": "#bfe3b4",
}


# ---------------------------------------------------------------- fonty
def ensure_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, url in FONT_URLS.items():
        path = os.path.join(FONT_DIR, name)
        if not os.path.exists(path):
            print("pobieram", name)
            urllib.request.urlretrieve(url, path)


_fonts = {}


def font(name, **axes):
    key = (name, tuple(sorted(axes.items())))
    if key not in _fonts:
        tt = instantiateVariableFont(TTFont(os.path.join(FONT_DIR, name)), axes)
        buf = io.BytesIO()
        tt.save(buf)
        data = buf.getvalue()
        _fonts[key] = (TTFont(io.BytesIO(data)), hb.Font(hb.Face(hb.Blob(data))))
    return _fonts[key]


BALOO = lambda w: font("Baloo2.ttf", wght=w)
NUNITO = lambda w: font("NunitoSans.ttf", wght=w, wdth=100, opsz=12, YTLC=500)


class Text:
    """Napis zamieniony na krzywe; linia bazowa w y=0, start w x=0."""

    def __init__(self, f, text, size, tracking=0.0, accent=False):
        tt, hbfont = f
        upem = tt["head"].unitsPerEm
        scale = size / upem
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hbfont, buf, {"kern": True, "liga": True})
        gs = tt.getGlyphSet()
        order = tt.getGlyphOrder()
        x = 0.0
        parts, accents = [], []
        fmt = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
        bp = BoundsPen(gs)
        n = len(buf.glyph_infos)
        for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
            gname = order[info.codepoint]
            ch = text[info.cluster]
            t = (scale, 0, 0, -scale, x + pos.x_offset * scale, -pos.y_offset * scale)
            sp = SVGPathPen(gs, ntos=fmt)
            gs[gname].draw(TransformPen(bp, t))
            glyph = tt["glyf"][gname]
            if accent and ch == "ś" and glyph.isComposite():
                # kreska nad „ś” w kolorze słońca: rysujemy komponenty osobno
                for comp in glyph.components:
                    cp = SVGPathPen(gs, ntos=fmt)
                    ct = (scale, 0, 0, -scale, t[4] + comp.x * scale, t[5] - comp.y * scale)
                    gs[comp.glyphName].draw(TransformPen(cp, ct))
                    (accents if comp.glyphName.startswith("acute") else parts).append(cp.getCommands())
            else:
                gs[gname].draw(TransformPen(sp, t))
                parts.append(sp.getCommands())
            x += pos.x_advance * scale + (size * tracking if i < n - 1 else 0)
        self.d = "".join(parts)
        self.accent_d = "".join(accents)
        x0, y0, x1, y1 = bp.bounds
        self.bounds = (x0, y0, x1, y1)
        self.w = x1 - x0
        self.top, self.bottom = y0, y1

    def svg(self, x, y, color, accent_color=None):
        """Rysuje napis tak, by lewa krawędź tuszu była w x, a linia bazowa w y."""
        tr = f'translate({x - self.bounds[0]:.2f} {y:.2f})'
        out = f'<path transform="{tr}" fill="{color}" d="{self.d}"/>'
        if self.accent_d:
            out += f'<path transform="{tr}" fill="{accent_color or color}" d="{self.accent_d}"/>'
        return out


# ---------------------------------------------------------------- sygnet
# Scena sygnetu to lista warstw (rola, element). Rola decyduje o kolorze w danej
# wersji kolorystycznej; rola zmapowana na KNOCK wycina przezroczystą dziurę we
# wszystkim, co narysowano wcześniej (maska), a SKIP pomija warstwę.
KNOCK, SKIP = "knock", "skip"

ARCH = "M20 100V52a40 40 0 0 1 80 0v48a12 12 0 0 1-12 12H32a12 12 0 0 1-12-12z"
SQUIRCLE = "M0 30C0 6 6 0 30 0h60c24 0 30 6 30 30v60c0 24-6 30-30 30H30C6 120 0 114 0 90z"
TOWER = "M60 23 64.2 50V58L71 65V116H49V65L55.8 58V50Z"
HILL = "M-10 96C12 84 30 85 46 89 62 93 74 98 88 91 100 85 112 84 130 88V130H-10Z"
HILL_EDGE = "M-10 96C12 84 30 85 46 89 62 93 74 98 88 91 100 85 112 84 130 88"


def el(tag, **a):
    return (tag, {k.rstrip("_").replace("_", "-"): v for k, v in a.items()})


def sun(cx, cy, r, face=True, rays=8, gap=3.2):
    L = []
    import math
    r0, r1 = r + 5.2, r + 10
    ray_d = ""
    for i in range(rays):
        a = math.radians(i * 360 / rays - 90 + 22.5)
        ray_d += f"M{cx + r0 * math.cos(a):.2f} {cy + r0 * math.sin(a):.2f}L{cx + r1 * math.cos(a):.2f} {cy + r1 * math.sin(a):.2f}"
    # szczelina oddzielająca słońce od łuku
    if gap:
        L.append(("gap", el("circle", cx=cx, cy=cy, r=r + gap)))
        L.append(("gap", el("path", d=ray_d, stroke_width=4.2 + 2 * gap, stroke_linecap="round", fill="none")))
    L.append(("sun", el("circle", cx=cx, cy=cy, r=r)))
    L.append(("sun", el("path", d=ray_d, stroke_width=4.2, stroke_linecap="round", fill="none")))
    if face:
        k = r / 14
        f = lambda dx, dy: f"{cx + dx * k:.2f} {cy + dy * k:.2f}"
        L.append(("cheek", el("circle", cx=cx - 7.6 * k, cy=cy + 3.4 * k, r=1.9 * k)))
        L.append(("cheek", el("circle", cx=cx + 7.6 * k, cy=cy + 3.4 * k, r=1.9 * k)))
        face_d = (f"M{f(-7, -1.5)}Q{f(-4.5, -4.8)} {f(-2, -1.5)}"
                  f"M{f(2, -1.5)}Q{f(4.5, -4.8)} {f(7, -1.5)}"
                  f"M{f(-5.2, 3.4)}Q{f(0, 9)} {f(5.2, 3.4)}")
        L.append(("face", el("path", d=face_d, stroke_width=1.9 * k, stroke_linecap="round", fill="none")))
    return L


def ladybug(cx, cy, s=1.0, rot=0):
    g = f"translate({cx} {cy}) rotate({rot}) scale({s})"
    return [
        ("gap_mono", el("ellipse", cx=0, cy=0, rx=8.6, ry=9.6, transform=g)),
        ("bug_d", el("circle", cx=0, cy=-6.4, r=4, transform=g)),
        ("gap_mono", el("path", d="M-4.6 -3.4Q0 -5.6 4.6 -3.4", stroke_width=2, fill="none", transform=g)),
        ("red", el("ellipse", cx=0, cy=1, rx=7, ry=7.6, transform=g)),
        ("bug_spot", el("path", d="M0 -5.4V8.4", stroke_width=1.3, fill="none", transform=g)),
        ("bug_spot", el("circle", cx=-3.4, cy=0, r=1.6, transform=g)),
        ("bug_spot", el("circle", cx=3.4, cy=-.6, r=1.6, transform=g)),
        ("bug_spot", el("circle", cx=-2.8, cy=5, r=1.4, transform=g)),
        ("bug_spot", el("circle", cx=3, cy=4.6, r=1.4, transform=g)),
    ]


def butterfly(cx, cy, s=1.0, rot=0):
    g = f"translate({cx} {cy}) rotate({rot}) scale({s})"
    return [
        ("blue", el("path", d="M0 -1C-4 -12-17-15-17-6c0 6 8 8 17 7z", transform=g)),
        ("blue", el("path", d="M0 -1C4 -12 17-15 17-6c0 6-8 8-17 7z", transform=g)),
        ("blue_l", el("path", d="M0 1C-9 1-14 6-11 11 8 13 0 6 0 1z", transform=g)),
        ("blue_l", el("path", d="M0 1C9 1 14 6 11 11-8 13 0 6 0 1z", transform=g)),
        ("gap_mono", el("path", d="M0 -6V10", stroke_width=5.4, stroke_linecap="round", fill="none", transform=g)),
        ("bug_d", el("path", d="M0 -6V10", stroke_width=2.6, stroke_linecap="round", fill="none", transform=g)),
        ("bug_d", el("path", d="M-.6 -6.5Q-2 -11-5 -12.5M.6 -6.5Q2 -11 5 -12.5", stroke_width=1.2, stroke_linecap="round", fill="none", transform=g)),
    ]


def bee(cx, cy, s=1.0, rot=0):
    g = f"translate({cx} {cy}) rotate({rot}) scale({s})"
    return [
        ("gap_mono", el("ellipse", cx=-3, cy=-8, rx=6.6, ry=4.6, transform=g + " rotate(-25)")),
        ("gap_mono", el("ellipse", cx=3.6, cy=-8.4, rx=6.6, ry=4.6, transform=g + " rotate(20)")),
        ("wing", el("ellipse", cx=-3, cy=-8, rx=5, ry=3.2, transform=g + " rotate(-25)")),
        ("wing", el("ellipse", cx=3.6, cy=-8.4, rx=5, ry=3.2, transform=g + " rotate(20)")),
        ("gap_mono", el("ellipse", cx=0, cy=0, rx=10, ry=7.4, transform=g)),
        ("amber", el("ellipse", cx=0, cy=0, rx=8.4, ry=5.9, transform=g)),
        ("bug_spot", el("path", d="M-2.4 -5.6V5.6M2.6 -5.4V5.4", stroke_width=2.2, fill="none", transform=g)),
        ("bug_spot", el("path", d="M8.2 0h3", stroke_width=1.6, stroke_linecap="round", fill="none", transform=g)),
    ]


def symbol_layers(variant):
    """variant: 'full' (z owadami), 'mini' (uproszczony), 'icon' (kafelek)."""
    container = SQUIRCLE if variant == "icon" else ARCH
    clip = "container"
    L = [("arch", el("path", d=container))]
    if variant == "icon":
        L += sun(33, 35, 14, face=True, gap=0)
    elif variant == "full":
        L += sun(27, 32, 14, face=True)
    else:
        L += sun(27, 32, 14.5, face=False, rays=8)
    L.append(("tower", el("path", d=TOWER)))
    L.append(("cross", el("path", d="M60 12.6V21.4M56.4 15.8H63.6", stroke_width=2.6, stroke_linecap="round", fill="none")))
    L.append(("window", el("circle", cx=60, cy=76.5, r=4.2)))
    L.append(("hill_gap", el("path", d=HILL_EDGE, stroke_width=4, fill="none", clip=clip)))
    L.append(("hill", el("path", d=HILL, clip=clip)))
    if variant == "full":
        L += ladybug(34, 100, 0.78, -14)
        L += bee(85, 62, 0.82, -8)
        L += butterfly(103, 22, 0.78, 14)
    else:
        L.append(("red", el("circle", cx=32, cy=100.5, r=4.4, clip=clip)))
        L.append(("amber", el("circle", cx=82, cy=100, r=4.4, clip=clip)))
        L.append(("blue", el("circle", cx=94, cy=95, r=4.4, clip=clip)))
    return L, container


# mapowanie ról na kolory dla wersji kolorystycznych
PALETTES = {
    "kolor": {
        "arch": C["leaf"], "gap": KNOCK, "sun": C["sun"], "face": C["sun_d"], "cheek": C["cheek"],
        "tower": C["cream"], "cross": C["sun"], "window": C["leaf"], "hill_gap": SKIP,
        "hill": C["grass"], "red": C["red"], "blue": C["blue"], "blue_l": C["blue_l"],
        "amber": C["amber"], "bug_d": C["bug_d"], "bug_spot": C["bug_d"], "wing": C["wing"],
        "gap_mono": SKIP,
        "text_top": C["leaf"], "text_main": C["ink"], "text_sub": C["leaf"], "text_accent": C["sun"],
    },
    "negatyw": {
        "arch": C["paper"], "gap": KNOCK, "sun": C["sun"], "face": C["sun_d"], "cheek": C["cheek"],
        "tower": KNOCK, "cross": C["leaf"], "window": C["paper"], "hill_gap": SKIP,
        "hill": C["grass"], "red": C["red"], "blue": C["blue"], "blue_l": C["blue_l"],
        "amber": C["amber"], "bug_d": C["bug_d"], "bug_spot": C["bug_d"], "wing": C["wing"],
        "gap_mono": SKIP,
        "text_top": C["mint"], "text_main": C["paper"], "text_sub": C["mint"], "text_accent": C["sun"],
    },
}


def mono(color):
    roles = {r: color for r in ["arch", "sun", "window", "hill", "red", "blue", "blue_l", "amber", "bug_d", "wing",
                                "text_top", "text_main", "text_sub", "text_accent"]}
    roles.update({r: KNOCK for r in ["gap", "face", "tower", "cross", "hill_gap", "bug_spot", "gap_mono"]})
    roles["cheek"] = SKIP
    return roles


PALETTES["mono"] = mono(C["ink"])
PALETTES["biale"] = mono("#ffffff")
PALETTES["zielone"] = mono(C["leaf"])


def attrs(a, paint):
    a = dict(a)
    clip = a.pop("clip", None)
    stroked = "stroke-width" in a
    if stroked:
        a["stroke"] = paint
        a.setdefault("fill", "none")
        a.setdefault("stroke-linejoin", "round")
    else:
        a["fill"] = paint
    s = " ".join(f'{k}="{v}"' for k, v in a.items())
    return s, clip


class Ids:
    def __init__(self, prefix):
        self.p, self.n = prefix, 0

    def __call__(self, kind):
        self.n += 1
        return f"{self.p}-{kind}{self.n}"


def render_symbol(variant, palette, ids, transform=""):
    """Zwraca (defs, body) — knock-outy robione maskami, więc tło może być dowolne."""
    layers, container = symbol_layers(variant)
    defs = []
    clip_id = ids("c")
    defs.append(f'<clipPath id="{clip_id}"><path d="{container}"/></clipPath>')
    body = ""
    pending_knock = []

    def flush():
        nonlocal body
        if not pending_knock:
            return
        mid = ids("m")
        holes = "".join(pending_knock)
        defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="-20" y="-20" width="160" height="160">'
                    f'<rect x="-20" y="-20" width="160" height="160" fill="#fff"/>{holes}</mask>')
        body = f'<g mask="url(#{mid})">{body}</g>'
        pending_knock.clear()

    for role, (tag, a) in layers:
        paint = palette[role]
        if paint == SKIP:
            continue
        if paint == KNOCK:
            s, clip = attrs(a, "#000")
            cp = f' clip-path="url(#{clip_id})"' if clip else ""
            pending_knock.append(f"<{tag} {s}{cp}/>")
            continue
        flush()
        s, clip = attrs(a, paint)
        cp = f' clip-path="url(#{clip_id})"' if clip else ""
        body += f"<{tag} {s}{cp}/>"
    flush()
    tr = f' transform="{transform}"' if transform else ""
    return "".join(defs), f"<g{tr}>{body}</g>"


# ---------------------------------------------------------------- układy
def svg_doc(w, h, defs, body, title, bg=None):
    bgr = f'<rect width="{w:.1f}" height="{h:.1f}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w:.0f}" height="{h:.0f}" role="img">'
            f"<title>{title}</title><defs>{defs}</defs>{bgr}{body}</svg>\n")


TITLE = "Przedszkole św. Jacka w Straszynie"


def texts():
    return {
        "top": Text(NUNITO(850), "PRZEDSZKOLE", 14.5, tracking=0.2),
        "main": Text(BALOO(800), "św. Jacka", 64, tracking=-0.005, accent=True),
        "sub": Text(BALOO(600), "w Straszynie", 28),
        "formal_top": Text(NUNITO(850), "PRZEDSZKOLE NIEPUBLICZNE", 13.2, tracking=0.2),
        "formal_main": Text(BALOO(700), "przy Parafii św. Jacka", 44, tracking=-0.005, accent=True),
        "formal_sub": Text(BALOO(600), "w Straszynie", 25),
        "compact_main": Text(BALOO(800), "Przedszkole św. Jacka", 40, tracking=-0.005, accent=True),
        "compact_sub": Text(BALOO(600), "w Straszynie", 23),
    }


def stack_lines(lines, x_of, top):
    """lines: [(Text, gap_before, role)]; układa napisy od góry wg rzeczywistego tuszu."""
    out, y = [], top
    for t, gap, role in lines:
        y += gap
        base = y - t.top
        out.append((t, x_of(t), base, role))
        y = base + t.bottom
    return out, y - top


def text_svg(placed, pal):
    return "".join(t.svg(x, b, pal["text_" + role], pal["text_accent"]) for t, x, b, role in placed)


def lockup_horizontal(pal, ids, T, keys=("top", "main", "sub"), gaps=(0, 10, 9), sym_variant="full"):
    sym = 120
    tx = sym + 20
    lines = [(T[keys[0]], gaps[0], "top"), (T[keys[1]], gaps[1], "main"), (T[keys[2]], gaps[2], "sub")]
    _, hgt = stack_lines(lines, lambda t: tx, 0)
    top = 62 - hgt / 2  # środek optyczny łuku
    placed, _ = stack_lines(lines, lambda t: tx, top)
    w = tx + max(t.w for t, *_ in placed) + 2
    defs, body = render_symbol(sym_variant, pal, ids)
    return w, 120, defs, body + text_svg(placed, pal)


def lockup_compact(pal, ids, T):
    sym = 120
    tx = sym + 18
    lines = [(T["compact_main"], 0, "main"), (T["compact_sub"], 9, "sub")]
    _, hgt = stack_lines(lines, lambda t: tx, 0)
    placed, _ = stack_lines(lines, lambda t: tx, 63 - hgt / 2)
    w = tx + max(t.w for t, *_ in placed) + 2
    defs, body = render_symbol("mini", pal, ids)
    return w, 120, defs, body + text_svg(placed, pal)


def lockup_stacked(pal, ids, T):
    tw = max(T["top"].w, T["main"].w, T["sub"].w)
    w = max(tw, 150) + 4
    sx = (w - 150) / 2
    lines = [(T["top"], 0, "top"), (T["main"], 10, "main"), (T["sub"], 9, "sub")]
    placed, hgt = stack_lines(lines, lambda t: (w - t.w) / 2, 150 + 22)
    defs, body = render_symbol("full", pal, ids, transform=f"translate({sx:.2f} 0) scale(1.25)")
    return w, 150 + 22 + hgt + 2, defs, body + text_svg(placed, pal)


def symbol_only(variant):
    def f(pal, ids, T):
        defs, body = render_symbol(variant, pal, ids)
        return 120, 120, defs, body
    return f


LAYOUTS = {
    "logo-poziome": lambda p, i, T: lockup_horizontal(p, i, T),
    "logo-pionowe": lockup_stacked,
    "logo-kompaktowe": lockup_compact,
    "logo-formalne": lambda p, i, T: lockup_horizontal(p, i, T, ("formal_top", "formal_main", "formal_sub"), (0, 9, 8)),
    "sygnet": symbol_only("full"),
    "sygnet-mini": symbol_only("mini"),
    "ikona": symbol_only("icon"),
}


def main():
    ensure_fonts()
    os.makedirs(OUT, exist_ok=True)
    T = texts()
    count = 0
    for name, fn in LAYOUTS.items():
        for pname, pal in PALETTES.items():
            if name == "ikona" and pname != "kolor":
                continue
            ids = Ids(f"{name}-{pname}")
            w, h, defs, body = fn(pal, ids, T)
            suffix = "" if pname == "kolor" else f"-{pname}"
            with open(os.path.join(OUT, f"{name}{suffix}.svg"), "w", encoding="utf-8") as fh:
                fh.write(svg_doc(w, h, defs, body, TITLE))
            count += 1
    print(f"zapisano {count} plików SVG w {OUT}")


if __name__ == "__main__":
    main()
