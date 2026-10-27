#!/usr/bin/env python3
"""Build the printable fill-in cheat sheet from ballot.json.

Usage: python build_cheatsheet.py ballot.json cheatsheet.html
Then:  python render_pdf.py cheatsheet.html cheatsheet.pdf --one-page

Every contest (contested AND uncontested) appears in exact ballot order.
Sections become divider bars; a contest may also carry "divider_before": "Page 2".
"""
import sys
from common import E, party, load, is_measure


def contest_html(n, c):
    office = c.get("short") or c["office"]
    if is_measure(c):
        rows = "".join(f'<div class="c"><span class="box"></span><span class="nm">{E(ch)}</span></div>'
                       for ch in c.get("choices", ["Yes", "No"]))
        return f'<div class="race" data-contest="{n}"><div class="of"><span class="n">{n}</span>{E(office)}</div>{rows}</div>'

    cands = c.get("candidates", [])
    ranked = c.get("ranked")
    vf = c.get("vote_for", 1)
    single = len(cands) == 1 and not c.get("writein")
    if ranked:
        k = c.get("max_ranks", min(len(cands) + (1 if c.get("writein") else 0), 5))
        head = "".join(f"<span>{i}</span>" for i in range(1, k + 1))
        names = [(x["name"], x.get("party")) for x in cands] + ([("Write-in ________", None)] if c.get("writein") else [])
        rows = f'<div class="rk hd"><span class="nm">Rank →</span>{head}</div>'
        for nm, p in names:
            tag, pcls, _ = party(p) if p is not None else ("", "np", "")
            boxes = '<span class="box"></span>' * k
            dc = f' data-cand="{E(nm)}"' if p is not None else ""
            rows += f'<div class="rk"{dc}><span class="nm">{E(nm)}' + (f' <span class="pt {pcls}">{E(tag)}</span>' if tag else "") + f'</span>{boxes}</div>'
        return (f'<div class="race" data-contest="{n}"><div class="of"><span class="n">{n}</span>{E(office)}'
                f'<span class="uo">rank up to {k}</span></div>{rows}</div>')

    rows = ""
    for x in cands:
        tag, pcls, _ = party(x.get("party"))
        rows += (f'<div class="c" data-cand="{E(x["name"])}"><span class="box"></span><span class="nm">{E(x["name"])}</span>'
                 + (f'<span class="pt {pcls}">{E(tag)}</span>' if tag else "") + "</div>")
    if c.get("writein"):
        rows += '<div class="c"><span class="box"></span><span class="nm wi">Write-in ________</span></div>'
    note = '<span class="uo">unopposed</span>' if single else (f'<span class="uo">vote for {vf}</span>' if vf > 1 else "")
    return f'<div class="race" data-contest="{n}"><div class="of"><span class="n">{n}</span>{E(office)}{note}</div>{rows}</div>'


def build(data):
    el, vi = data["election"], data.get("voting_info", {})
    out, n = [], 0
    for s in data["sections"]:
        out.append(f'<div class="pg">{E(s.get("ballot_label") or s["title"])}</div>')
        for c in s["contests"]:
            if c.get("divider_before"):
                out.append(f'<div class="pg">{E(c["divider_before"])}</div>')
            n += 1
            out.append(contest_html(n, c))
    remind = vi.get("cheatsheet_reminder", "Bring any required ID. Check your state's rules on phones and notes in the voting booth.")
    sub = " · ".join(x for x in (el.get("jurisdiction"), el.get("precinct"), el.get("date_label")) if x)
    two = data.get("cheatsheet_two_sided")
    return f'''<title>Ballot Cheat Sheet</title>
<style>
@page {{ size: letter; margin: 0.32in 0.3in 0.3in; }}
:root {{ --fs: 8pt; }}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; background: #fff; color: #111; font: var(--fs)/1.2 "Liberation Sans Narrow", "Arial Narrow", "DejaVu Sans Condensed", Arial, sans-serif; }}
header {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 12pt; border-bottom: 1.5pt solid #111; padding-bottom: 3pt; margin-bottom: 4pt; }}
h1 {{ font-size: calc(var(--fs) * 1.7); margin: 0; }}
.sub {{ font-size: calc(var(--fs) * .95); text-align: right; }}
.how {{ font-size: calc(var(--fs) * .93); margin: 0 0 4pt; }}
.cols {{ column-count: 4; column-gap: 9pt; column-rule: 0.5pt solid #bbb; }}
.pg {{ break-after: avoid; font-weight: 700; font-size: calc(var(--fs) * .85); text-transform: uppercase; letter-spacing: .06em; background: #222; color: #fff; padding: 1pt 3pt; margin: 3pt 0 2pt; }}
.race {{ break-inside: avoid; border-bottom: 0.4pt solid #ccc; padding: 1.4pt 0 1.6pt; }}
.of {{ font-weight: 700; display: flex; gap: 3pt; align-items: baseline; }}
.n {{ font-weight: 400; color: #555; min-width: 1.4em; font-variant-numeric: tabular-nums; }}
.uo {{ font-weight: 400; font-style: italic; color: #555; margin-left: auto; white-space: nowrap; }}
.c {{ display: flex; align-items: center; gap: 3pt; padding-left: 1.6em; }}
.box {{ width: .92em; height: .92em; border: 0.8pt solid #111; flex: none; }}
.nm {{ flex: 1; min-width: 0; }} .wi {{ color: #555; }}
.pt {{ font-size: .8em; font-weight: 700; }}
.rep {{ color: #c0392b; }} .dem {{ color: #1f5bc4; }} .lib {{ color: #a07400; }} .grn {{ color: #2f8a43; }} .oth {{ color: #8a3fa8; }} .np {{ color: #5f6b85; }}
.rk {{ display: flex; align-items: center; gap: 2pt; padding-left: 1.6em; }}
.rk.hd span:not(.nm) {{ width: .92em; text-align: center; font-size: .8em; color: #555; }}
.rk.hd .nm {{ color: #555; font-size: .85em; }}
footer {{ margin-top: 3pt; font-size: calc(var(--fs) * .8); color: #444; border-top: 0.5pt solid #999; padding-top: 2pt; }}
</style>
<header><h1>MY BALLOT CHEAT SHEET</h1><div class="sub">{E(sub)}</div></header>
<p class="how"><b>How to use:</b> Mark your choices before you go. Every contest is listed in ballot order, including uncontested ones, and the numbers match the research guide. On multi-column ballots, work down the left column, then the right. A blank contest is skipped; the rest of your ballot still counts. {E(remind)}</p>
<div class="cols">{"".join(out)}</div>
<footer>{n} contests{" · print double-sided" if two else ""}. Uncontested races list one name; you may vote for that candidate or leave it blank. Check names against the official ballot; this sheet is a personal reminder only.</footer>
'''


if __name__ == "__main__":
    d = load(sys.argv[1])
    open(sys.argv[2], "w").write(build(d))
    print("wrote", sys.argv[2])
