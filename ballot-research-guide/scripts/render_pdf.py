#!/usr/bin/env python3
"""Render a guide or cheat-sheet HTML file to a Letter-size PDF with headless Chromium.

Usage:
  python render_pdf.py guide.html guide.pdf [--footer "Ballot Guide"]
  python render_pdf.py cheatsheet.html cheatsheet.pdf --one-page

--one-page shrinks the cheat sheet's base font (CSS var --fs) until it fits one page
(stops at 6pt and reports if it still doesn't fit; then print double-sided).
Requires: pip install playwright && python -m playwright install chromium
"""
import argparse
import os
import re
import tempfile
from playwright.sync_api import sync_playwright


def pages(pdf_bytes):
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--footer", default=None)
    ap.add_argument("--one-page", action="store_true")
    a = ap.parse_args()

    src = open(a.src).read()
    if not src.lstrip().lower().startswith("<!doctype"):
        src = ('<!doctype html><html><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width">' + src + "</html>")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
    tmp.write(src)
    tmp.close()

    opts = dict(format="Letter", print_background=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + os.path.abspath(tmp.name))
        pg.wait_for_timeout(1500)  # web fonts; falls back cleanly if blocked
        pg.emulate_media(media="print", color_scheme="light")
        if a.one_page:
            opts["prefer_css_page_size"] = True
            size = 9.0
            while True:
                pg.evaluate(f"document.documentElement.style.setProperty('--fs','{size}pt')")
                data = pg.pdf(**opts)
                if pages(data) <= 1 or size <= 6.0:
                    break
                size = round(size - 0.25, 2)
            print(f"font {size}pt, {pages(data)} page(s)")
        else:
            opts["margin"] = dict(top="0.5in", bottom="0.6in", left="0.5in", right="0.5in")
            if a.footer:
                opts.update(display_header_footer=True, header_template="<span></span>",
                            footer_template=f'<div style="font-size:8px;width:100%;text-align:center;color:#666">'
                                            f'{a.footer} · page <span class="pageNumber"></span> of <span class="totalPages"></span></div>')
            data = pg.pdf(**opts)
            print(f"{pages(data)} page(s)")
        b.close()
    open(a.out, "wb").write(data)
    os.unlink(tmp.name)


if __name__ == "__main__":
    main()
