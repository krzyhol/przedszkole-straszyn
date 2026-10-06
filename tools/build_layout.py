#!/usr/bin/env python3
"""
Generuje wspólne elementy wszystkich stron serwisu.

1. Nagłówek i stopka — edytuje się wyłącznie w plikach:
     _partials/header.html
     _partials/footer.html
   Skrypt podmienia <header>…</header> i <footer>…</footer> w każdym pliku
   *.html w katalogu głównym. Szablony są pisane tak jak dla podstrony
   (linki "index.html#o-nas"); skrypt sam dopasowuje je do strony:
     - na stronie głównej linki "index.html#…" zamienia na "#…",
       a "index.html" na "#start",
     - w menu oznacza bieżącą stronę atrybutem aria-current="page".

2. Metadane SEO w <head> (blok między <!-- seo: … --> a <!-- /seo -->):
   adres kanoniczny, Open Graph (podgląd linku na Facebooku/Messengerze),
   a na stronie głównej dane strukturalne JSON-LD. Tytuł i opis są brane
   z <title> i <meta name="description"> danej strony.

3. Wersje plików CSS/JS (?v=…) — skrót zawartości pliku, żeby po zmianie
   przeglądarki nie pokazywały starej wersji z pamięci podręcznej.

4. sitemap.xml i robots.txt.

Po podpięciu własnej domeny wystarczy zmienić SITE_URL i uruchomić skrypt.

Użycie:     python3 tools/build_layout.py           (aktualizuje pliki)
            python3 tools/build_layout.py --check   (tylko sprawdza, kod 1 = nieaktualne)
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "_partials"
HOME = "index.html"

SITE_URL = "https://krzyhol.github.io/przedszkole-straszyn/"
SITE_NAME = "Przedszkole św. Jacka w Straszynie"
NOINDEX = {"404.html"}  # strony poza wyszukiwarką i mapą strony
OG_IMAGE = {"path": "brand/favicon/og-image.png", "width": 1200, "height": 630,
            "alt": "Logo Przedszkola św. Jacka w Straszynie"}
ASSETS = ["assets/css/fonts.css", "assets/css/style.css", "assets/js/main.js"]
EXTRA_PAGES = [ROOT / "brand" / "index.html"]  # tylko wersje plików, bez nagłówka i SEO

# dane organizacji dla Google (schema.org) — wyświetlane m.in. w wynikach wyszukiwania i Mapach
ORGANIZATION = {
    "@context": "https://schema.org",
    "@type": ["Preschool", "ChildCare"],
    "name": SITE_NAME,
    "alternateName": "Niepubliczne Przedszkole św. Jacka w Straszynie",
    "url": SITE_URL,
    "logo": SITE_URL + "brand/logo/png/logo-formalne.png",
    "image": SITE_URL + "assets/img/budynek-1400.webp",
    "telephone": "+48507700418",
    "email": "przedszkole@straszyn.org",
    "foundingDate": "2003",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "ul. Poprzeczna 24",
        "postalCode": "83-010",
        "addressLocality": "Straszyn",
        "addressCountry": "PL",
    },
    "openingHoursSpecification": [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "opens": "06:00",
        "closes": "17:30",
    }],
    "parentOrganization": {
        "@type": "Organization",
        "name": "Parafia Rzymskokatolicka pw. św. Jacka Odrowąża w Straszynie",
    },
}

BLOCKS = {
    "header": re.compile(r"(?:<!-- header: generowany[^\n]*-->\n)?<header>.*?</header>", re.S),
    "footer": re.compile(r"(?:<!-- footer: generowany[^\n]*-->\n)?<footer>.*?</footer>", re.S),
}
NOTE = "<!-- {name}: generowany z _partials/{name}.html — edytuj szablon i uruchom tools/build_layout.py -->\n"
SEO_BLOCK = re.compile(r"<!-- seo: .*?<!-- /seo -->\n", re.S)
DESCRIPTION = re.compile(r'<meta name="description" content="([^"]*)">\n')


def render(name: str, page: str) -> str:
    html = (PARTIALS / f"{name}.html").read_text().rstrip("\n")
    if page == HOME:
        html = html.replace('href="index.html#', 'href="#').replace('href="index.html"', 'href="#start"')
    if name == "header":
        # oznacz bieżącą stronę w menu
        html = re.sub(rf'(<li><a href="{re.escape(page)}"[^>]*)>', r'\1 aria-current="page">', html)
    return NOTE.format(name=name) + html


def page_url(page: str) -> str:
    return SITE_URL if page == HOME else SITE_URL + page


def render_seo(page: str, text: str) -> str:
    lines = ["<!-- seo: generowane przez tools/build_layout.py — nie edytuj ręcznie -->"]
    if page in NOINDEX:
        lines.append('<meta name="robots" content="noindex">')
    else:
        title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
        description = DESCRIPTION.search(text).group(1)
        url = page_url(page)
        lines += [
            f'<link rel="canonical" href="{url}">',
            '<meta property="og:type" content="website">',
            '<meta property="og:locale" content="pl_PL">',
            f'<meta property="og:site_name" content="{SITE_NAME}">',
            f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{description}">',
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:image" content="{SITE_URL}{OG_IMAGE["path"]}">',
            f'<meta property="og:image:width" content="{OG_IMAGE["width"]}">',
            f'<meta property="og:image:height" content="{OG_IMAGE["height"]}">',
            f'<meta property="og:image:alt" content="{OG_IMAGE["alt"]}">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
        if page == HOME:
            data = dict(ORGANIZATION, description=description)
            lines.append('<script type="application/ld+json">\n'
                         + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>")
    lines.append("<!-- /seo -->")
    return "\n".join(lines) + "\n"


def asset_versions() -> dict:
    return {a: hashlib.sha256((ROOT / a).read_bytes()).hexdigest()[:8] for a in ASSETS}


def stamp_assets(text: str, versions: dict) -> str:
    for asset, version in versions.items():
        text = re.sub(rf'((?:href|src)="(?:\.\./)?{re.escape(asset)})(?:\?v=[0-9a-f]+)?"',
                      rf'\1?v={version}"', text)
    return text


def build(path: pathlib.Path, versions: dict) -> str:
    text = path.read_text()
    for name, pattern in BLOCKS.items():
        if len(pattern.findall(text)) != 1:
            sys.exit(f"{path.name}: oczekiwano dokładnie jednego bloku <{name}>")
        block = render(name, path.name)
        text = pattern.sub(lambda _: block, text)

    seo = render_seo(path.name, text)
    if SEO_BLOCK.search(text):
        text = SEO_BLOCK.sub(lambda _: seo, text)
    elif DESCRIPTION.search(text):
        text = DESCRIPTION.sub(lambda m: m.group(0) + seo, text, count=1)
    else:
        sys.exit(f'{path.name}: brak <meta name="description"> — za nim wstawiany jest blok SEO')

    return stamp_assets(text, versions)


def render_sitemap(pages: list) -> str:
    urls = "".join(f"  <url><loc>{page_url(p)}</loc></url>\n" for p in pages)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")


def render_robots() -> str:
    # uwaga: wyszukiwarki czytają robots.txt tylko z głównego katalogu domeny,
    # więc pod adresem github.io/<repozytorium>/ zacznie działać dopiero z własną domeną
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n"


def main() -> None:
    check = "--check" in sys.argv[1:]
    versions = asset_versions()
    pages = sorted(ROOT.glob("*.html"), key=lambda p: (p.name != HOME, p.name))

    outputs = {path: build(path, versions) for path in pages}
    outputs.update({path: stamp_assets(path.read_text(), versions) for path in EXTRA_PAGES})
    outputs[ROOT / "sitemap.xml"] = render_sitemap([p.name for p in pages if p.name not in NOINDEX])
    outputs[ROOT / "robots.txt"] = render_robots()

    stale = []
    for path, new in outputs.items():
        old = path.read_text() if path.exists() else None
        if new != old:
            stale.append(str(path.relative_to(ROOT)))
            if not check:
                path.write_text(new)
    if check and stale:
        sys.exit("Nieaktualne pliki: " + ", ".join(stale) + "\nUruchom: python3 tools/build_layout.py")
    print(("Do aktualizacji: " if check else "Zaktualizowano: ") + (", ".join(stale) or "nic — wszystko aktualne"))


if __name__ == "__main__":
    main()
