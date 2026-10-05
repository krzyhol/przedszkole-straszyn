#!/usr/bin/env python3
"""
Wstawia wspólny nagłówek i stopkę do wszystkich stron serwisu.

Nagłówek i stopkę edytuje się wyłącznie w plikach:
  _partials/header.html
  _partials/footer.html
a potem uruchamia ten skrypt, który podmienia <header>…</header>
i <footer>…</footer> w każdym pliku *.html w katalogu głównym.

Szablony są pisane tak jak dla podstrony (linki "index.html#o-nas").
Skrypt sam dopasowuje je do strony:
  - na stronie głównej linki "index.html#…" zamienia na "#…",
    a "index.html" na "#start",
  - w menu oznacza bieżącą stronę atrybutem aria-current="page".

Użycie:     python3 tools/build_layout.py           (aktualizuje pliki)
            python3 tools/build_layout.py --check   (tylko sprawdza, kod 1 = nieaktualne)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "_partials"
HOME = "index.html"

BLOCKS = {
    "header": re.compile(r"(?:<!-- header: generowany[^\n]*-->\n)?<header>.*?</header>", re.S),
    "footer": re.compile(r"(?:<!-- footer: generowany[^\n]*-->\n)?<footer>.*?</footer>", re.S),
}
NOTE = "<!-- {name}: generowany z _partials/{name}.html — edytuj szablon i uruchom tools/build_layout.py -->\n"


def render(name: str, page: str) -> str:
    html = (PARTIALS / f"{name}.html").read_text().rstrip("\n")
    if page == HOME:
        html = html.replace('href="index.html#', 'href="#').replace('href="index.html"', 'href="#start"')
    if name == "header":
        # oznacz bieżącą stronę w menu
        html = re.sub(rf'(<li><a href="{re.escape(page)}"[^>]*)>', r'\1 aria-current="page">', html)
    return NOTE.format(name=name) + html


def build(path: pathlib.Path) -> str:
    text = path.read_text()
    for name, pattern in BLOCKS.items():
        if len(pattern.findall(text)) != 1:
            sys.exit(f"{path.name}: oczekiwano dokładnie jednego bloku <{name}>")
        block = render(name, path.name)
        text = pattern.sub(lambda _: block, text)
    return text


def main() -> None:
    check = "--check" in sys.argv[1:]
    stale = []
    for path in sorted(ROOT.glob("*.html")):
        new = build(path)
        if new != path.read_text():
            stale.append(path.name)
            if not check:
                path.write_text(new)
    if check and stale:
        sys.exit("Nieaktualny nagłówek/stopka: " + ", ".join(stale) + "\nUruchom: python3 tools/build_layout.py")
    print(("Do aktualizacji: " if check else "Zaktualizowano: ") + (", ".join(stale) or "nic — wszystko aktualne"))


if __name__ == "__main__":
    main()
