#!/usr/bin/env python3
"""
Sprawdza linki wewnętrzne serwisu: czy pliki, do których prowadzą href/src/srcset
(strony, obrazy, CSS, JS, czcionki) istnieją, i czy kotwice "#…" wskazują
na istniejące id na stronie docelowej. Sprawdza też url(…) w plikach CSS.

Linki zewnętrzne (http…, mailto:, tel:) są pomijane — ich dostępność zależy
od innych serwisów i nie powinna blokować zmian.

Użycie:     python3 tools/check_links.py      (kod 1 = znaleziono błędy)
"""
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html")) + [ROOT / "brand" / "index.html"]
SKIP = ("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []  # (atrybut, wartość, wiersz)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                self.ids.add(value)
            elif name in ("href", "src"):
                self.links.append((name, value, self.getpos()[0]))
            elif name == "srcset":
                for part in value.split(","):
                    self.links.append((name, part.split()[0], self.getpos()[0]))

    handle_startendtag = handle_starttag


def parse(path: pathlib.Path) -> Page:
    page = Page()
    page.feed(path.read_text())
    return page


def main() -> None:
    parsed = {p: parse(p) for p in PAGES}
    errors = []

    for path, page in parsed.items():
        where = path.relative_to(ROOT)
        for attr, value, line in page.links:
            if value.startswith(SKIP):
                continue
            url = urlsplit(value)
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if url.path and not target.exists():
                errors.append(f"{where}:{line}: {attr}=\"{value}\" — brak pliku")
                continue
            # "#top" to wbudowany w HTML skok na początek strony
            if url.fragment and url.fragment != "top" and target.suffix == ".html":
                ids = parsed[target].ids if target in parsed else parse(target).ids
                if url.fragment not in ids:
                    errors.append(f"{where}:{line}: {attr}=\"{value}\" — brak id=\"{url.fragment}\"")

    for css in sorted(ROOT.glob("assets/css/*.css")):
        for ref in re.findall(r"url\(\s*['\"]?([^'\")]+)", css.read_text()):
            if not ref.startswith(SKIP) and not (css.parent / ref).resolve().exists():
                errors.append(f"{css.relative_to(ROOT)}: url({ref}) — brak pliku")

    if errors:
        sys.exit("Zepsute linki:\n  " + "\n  ".join(errors))
    print(f"Linki wewnętrzne w porządku ({len(PAGES)} stron).")


if __name__ == "__main__":
    main()
