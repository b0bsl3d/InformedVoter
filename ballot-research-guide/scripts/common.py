"""Shared helpers for the ballot guide and cheat sheet builders."""
import html
import json

E = html.escape

# Party label -> (short tag, css class, full name)
_PARTY_MAP = [
    (("rep", "r", "republican", "gop"), ("REP", "rep", "Republican")),
    (("dem", "d", "democrat", "democratic", "dfl"), ("DEM", "dem", "Democrat")),
    (("lib", "l", "libertarian"), ("LIB", "lib", "Libertarian")),
    (("grn", "g", "green"), ("GRN", "grn", "Green")),
    (("np", "nonpartisan", "non-partisan", "", "none"), ("", "np", "Nonpartisan")),
]


def party(label):
    """Return (tag, css_class, full_name) for a free-text party label."""
    key = (label or "").strip().lower().rstrip(".")
    for keys, val in _PARTY_MAP:
        if key in keys:
            return val
    # Independents, Working Families, Constitution, etc.: purple "other" color
    tag = (label or "").strip()
    short = tag if len(tag) <= 4 else tag[:3].upper()
    return (short.upper(), "oth", tag)


def load(path):
    with open(path) as f:
        return json.load(f)


def is_measure(c):
    return c.get("type") == "measure"


def contested(c):
    return is_measure(c) or len(c.get("candidates", [])) > 1


def links_html(links, cls="links"):
    if not links:
        return ""
    inner = " ".join(
        f'<a href="{E(u)}" target="_blank" rel="noopener">{E(l)}</a>' for l, u in links)
    return f'<p class="{cls}">{inner}</p>'


PARTY_TOKENS_LIGHT = "--rep: #c0392b; --dem: #1f5bc4; --lib: #b07f00; --grn: #2f8a43; --oth: #8a3fa8; --np: #5f6b85;"
PARTY_TOKENS_DARK = "--rep: #e5574a; --dem: #4d8cf0; --lib: #e0b030; --grn: #4fb866; --oth: #c27fe0; --np: #9aa6c4;"


def standalone(fragment, marker='<div class="wrap">'):
    """Wrap an artifact-style fragment (title + style + content) into a complete HTML document
    that opens on its own in any browser, offline or as an email attachment."""
    i = fragment.find(marker)
    head, body = (fragment[:i], fragment[i:]) if i >= 0 else ("", fragment)
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
