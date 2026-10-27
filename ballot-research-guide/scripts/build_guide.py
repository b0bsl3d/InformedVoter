#!/usr/bin/env python3
"""Build the research guide page from ballot.json.

Usage: python build_guide.py ballot.json guide.html

Output is an artifact-ready HTML fragment (title + style + content, no <html>/<body>);
render_pdf.py wraps it into a full document for printing.
"""
import sys
from common import E, party, load, is_measure, contested, links_html, standalone, PARTY_TOKENS_LIGHT, PARTY_TOKENS_DARK


def bar_row(name, pcls, width, value_txt):
    return (f'<div class="bar-row"><span class="bn">{E(name)}</span>'
            f'<span class="track"><span class="fill {pcls}" style="width:{max(0, min(100, width)):.1f}%"></span></span>'
            f'<span class="bv">{E(value_txt)}</span></div>')


def poll_strip(c):
    cands = c["candidates"]
    pc = {x["name"]: party(x.get("party"))[1] for x in cands}
    blocks = []
    poll, prior = c.get("poll"), c.get("prior_result")
    if poll and poll.get("values"):
        vals = poll["values"]
        mx = max(60, max(vals.values()))
        rows = "".join(bar_row(x["name"], pc[x["name"]], (vals.get(x["name"]) or 0) / mx * 100,
                               f'{vals[x["name"]]}%' if x["name"] in vals else "n/a") for x in cands)
        blocks.append(f'<div class="ib"><p class="ib-t">Voter poll <span>{E(poll.get("source", ""))}</span></p>{rows}</div>')
    elif prior and prior.get("values"):
        vals = prior["values"]
        rows = "".join(bar_row(x["name"], pc[x["name"]], vals.get(x["name"], 0),
                               f'{vals[x["name"]]}%' if x["name"] in vals else "n/a") for x in cands)
        blocks.append(f'<div class="ib"><p class="ib-t">No voter poll found <span>{E(prior.get("label", "Prior result"))}</span></p>{rows}</div>')
    else:
        blocks.append('<div class="ib"><p class="ib-t">Voter poll</p><p class="none">No public poll found for this race.</p></div>')

    bp = c.get("bar_poll")
    if bp and bp.get("values"):
        vals = bp["values"]
        if bp.get("type") == "rating":
            # values: name -> [strongly rec, rec, neutral, not rec, strongly not rec, skipped] (percent)
            rows = ""
            for x in cands:
                v = vals.get(x["name"])
                if not v:
                    rows += bar_row(x["name"], pc[x["name"]], 0, "n/a")
                    continue
                rec, neu, neg = v[0] + v[1], v[2], v[3] + v[4]
                rows += (f'<div class="bar-row"><span class="bn">{E(x["name"])}</span><span class="track stack">'
                         f'<span class="fill {pc[x["name"]]}" style="width:{rec}%"></span>'
                         f'<span class="seg neu" style="width:{neu}%"></span><span class="seg neg" style="width:{neg}%"></span></span>'
                         f'<span class="bv">{rec:.0f}% / {neg:.0f}%</span></div>')
            rows += ('<p class="key"><i class="k rec"></i>Recommend <i class="k neu"></i>Neutral '
                     '<i class="k neg"></i>Not recommend <i class="k sk"></i>Skipped</p>')
        else:
            mx = max(vals.values()) or 1
            rows = "".join(bar_row(x["name"], pc[x["name"]], (vals.get(x["name"]) or 0) / mx * 100,
                                   f'{vals[x["name"]]:,}' if x["name"] in vals else "n/a") for x in cands)
        blocks.append(f'<div class="ib"><p class="ib-t">Bar poll <span>{E(bp.get("source", ""))}</span></p>{rows}</div>')
    else:
        judicial = c.get("judicial", any(w in c["office"] for w in ("Judge", "Justice", "Court")))
        txt = ("Bar poll results for this race were not found." if judicial
               else "No bar poll applies (non-judicial office).")
        blocks.append(f'<div class="ib"><p class="ib-t">Bar poll</p><p class="none">{txt}</p></div>')
    return '<div class="info">' + "".join(blocks) + "</div>"


def cand_card(x):
    tag, pcls, full = party(x.get("party"))
    tags = f'<span class="party {pcls}" title="{E(full)}">{E(tag)}</span>' if tag else ""
    if x.get("incumbent"):
        tags += '<span class="tag">Incumbent</span>'
    if x.get("thin"):
        tags += '<span class="tag thin">Little info</span>'
    facts = "".join(f"<li>{E(f)}</li>" for f in x.get("facts", []))
    return (f'<div class="cand" data-cand="{E(x["name"])}"><div class="cand-head"><h4>{E(x["name"])}</h4><div class="tags">{tags}</div></div>'
            f'<ul>{facts}</ul>{links_html(x.get("links"))}</div>')


def measure_cards(c):
    m = c.get("measure", {})
    cards = []
    for key, label in (("what", "What it does"), ("support", "Support"), ("opposition", "Opposition"), ("fiscal", "Fiscal / tax impact")):
        v = m.get(key)
        if not v:
            continue
        items = v if isinstance(v, list) else [v]
        cards.append(f'<div class="cand"><div class="cand-head"><h4>{label}</h4></div><ul>'
                     + "".join(f"<li>{E(i)}</li>" for i in items) + "</ul></div>")
    return cards


def issue_html(iss):
    tl = "".join(f'<li><b>{E(t[0])}:</b> {E(t[1])}</li>' for t in iss.get("timeline", []))
    tbl = ""
    st = iss.get("stance_table")
    if st:
        head = "".join(f"<th>{E(h)}</th>" for h in st["columns"])
        body = ""
        for row in st["rows"]:
            cells = []
            for i, cell in enumerate(row):
                if isinstance(cell, dict):  # {"lean": "r|d|n", "label": "...", "note": "..."}
                    cls = {"r": "rep", "d": "dem"}.get(cell.get("lean"), "muted")
                    cells.append(f'<td><span class="lean {cls}">{E(cell.get("label", ""))}</span> {E(cell.get("note", ""))}</td>')
                else:
                    cells.append(f"<td>{E(str(cell))}</td>")
            body += "<tr>" + "".join(cells) + "</tr>"
        tbl = f'<div class="tablewrap"><table class="stance"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    note = f'<p class="note">{E(iss["note"])}</p>' if iss.get("note") else ""
    return (f'<div class="race issue"><header class="race-head"><span class="num">§</span><div><h3>{E(iss["title"])}</h3>'
            f'<p class="meta">{E(iss.get("subtitle", "Background and where candidates stand"))}</p></div></header>'
            f'<div class="split-body"><ul class="timeline">{tl}</ul>{tbl}{note}{links_html(iss.get("links"))}</div></div>')


def build(data):
    el = data["election"]
    toc, body, n = [], [], 0
    issues = data.get("issues", [])
    for si, s in enumerate(data["sections"]):
        sid = f"s{si}"
        items, races = [], []
        first = n + 1
        for c in s["contests"]:
            n += 1
            rid = f"r{n}"
            page = f'Ballot page {E(str(c["ballot_page"]))} · ' if c.get("ballot_page") else ""
            if not contested(c):
                x = (c.get("candidates") or [{"name": "(no candidate listed)"}])[0]
                tag, pcls, full = party(x.get("party"))
                chip = f' <span class="party {pcls}">{E(tag)}</span>' if tag else ""
                items.append(f'<li class="toc-unc"><a href="#{rid}"><span class="num">{n}</span>{E(c["office"])} <i>(unopposed)</i></a></li>')
                races.append(f'<div class="unc-row" id="{rid}" data-contest="{n}"><span class="num">{n}</span>'
                             f'<span class="uo-office">{E(c["office"])}</span>'
                             f'<span class="uo-name" data-cand="{E(x["name"])}">{E(x["name"])}{chip}</span>'
                             f'<span class="uo-tag">Unopposed{(" · p." + E(str(c["ballot_page"]))) if c.get("ballot_page") else ""}</span></div>')
                continue
            items.append(f'<li><a href="#{rid}"><span class="num">{n}</span>{E(c["office"])}</a></li>')
            if is_measure(c):
                cards = measure_cards(c)
                meta = f'{page}{" / ".join(c.get("choices", ["Yes", "No"]))}'
                inner = f'<div class="cands c2">{"".join(cards)}</div>'
            else:
                k = len(c["candidates"])
                vf = c.get("vote_for", 1)
                meta = f'{page}{k} candidates' + (f' · vote for {vf}' if vf > 1 else "") + (" · ranked choice" if c.get("ranked") else "")
                inner = poll_strip(c) + f'<div class="cands c2">{"".join(cand_card(x) for x in c["candidates"])}</div>'
            races.append(
                f'<article class="race" id="{rid}" data-contest="{n}"><header class="race-head"><span class="num">{n}</span>'
                f'<div><h3>{E(c["office"])}</h3><p class="meta">{meta}</p></div></header>'
                + (f'<p class="office">{E(c["description"])}</p>' if c.get("description") else "")
                + inner + links_html(c.get("links"), "links race-links") + "</article>")
        pre = "".join(issue_html(i) for i in issues if i.get("before_section") in (si, s["title"]))
        if not races:
            continue
        rng = f'<span class="rng">#{first}–{n}</span>' if n > first else f'<span class="rng">#{first}</span>'
        toc.append(f'<li><a href="#{sid}">{E(s["title"])} {rng}</a><ol>{"".join(items)}</ol></li>')
        body.append(f'<section class="sec" id="{sid}"><h2>{E(s["title"])} {rng}</h2>'
                    + (f'<p class="sec-intro">{E(s["intro"])}</p>' if s.get("intro") else "")
                    + pre + "".join(races) + "</section>")

    vi = data.get("voting_info", {})
    vi_title = "First time voting? What to know in " + vi.get("state", "your state") if vi.get("audience") == "first_time" else "Voting basics for " + vi.get("state", "this election")
    vi_items = "".join(f'<li>{E(i["text"])}' + (f' <a href="{E(i["source"])}" target="_blank" rel="noopener">source</a>' if i.get("source") else "") + "</li>"
                       for i in vi.get("items", []))
    vi_html = f'<div class="notice"><b>{E(vi_title)}</b><ul>{vi_items}</ul></div>' if vi_items else ""
    qc = data.get("qc", {})
    qc_items = "".join(f"<li>{E(v)}</li>" for v in qc.get("items", []))
    qc_html = (f'<div class="notice qc"><b>Quality checks</b><ul>{qc_items}</ul></div>' if qc_items else
               '<div class="notice qc warn"><b>Quality checks not recorded.</b> Treat this guide as a draft.</div>')
    res = "".join(f'<li><a href="{E(u)}" target="_blank" rel="noopener">{E(l)}</a></li>' for l, u in data.get("resources", []))
    title = el.get("guide_title", "Ballot Guide")
    sub = " · ".join(x for x in (el.get("jurisdiction"), el.get("precinct"), el.get("date_label")) if x)

    return f'''<title>{E(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: ballot-style contests; each race is a ruled box with a dark contest band, poll strip, then candidates side by side. */
:root {{
  --paper: #fbfbf9; --ink: #1b2230; --muted: #5b6474; --rule: #c9ced6; --band: #26303f; --band-fg: #f3f5f8;
  --card: #ffffff; --soft: #eef1f5; --accent: #9a6b12; --link: #1f5aa6; --neu: #b9bfc8; --neg: #4a505b;
  {PARTY_TOKENS_LIGHT}
  --f-display: "IBM Plex Sans Condensed", "Arial Narrow", sans-serif;
  --f-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #13171e; --ink: #e5e8ee; --muted: #9aa3b2; --rule: #343c49; --band: #2b3546; --band-fg: #f3f5f8;
  --card: #1a1f28; --soft: #222935; --accent: #e0b35a; --link: #7fb0f0; --neu: #5a6170; --neg: #c9ced6;
  {PARTY_TOKENS_DARK} color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --paper: #13171e; --ink: #e5e8ee; --muted: #9aa3b2; --rule: #343c49; --band: #2b3546; --band-fg: #f3f5f8;
  --card: #1a1f28; --soft: #222935; --accent: #e0b35a; --link: #7fb0f0; --neu: #5a6170; --neg: #c9ced6;
  {PARTY_TOKENS_DARK} color-scheme: dark; }}
body {{ background: var(--paper); color: var(--ink); font: 16px/1.5 var(--f-body); }}
.wrap {{ max-width: 1040px; margin: 0 auto; padding-block: 32px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
h1, h2, h3, h4 {{ font-family: var(--f-display); text-wrap: balance; margin: 0; }}
a {{ color: var(--link); }} a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.kicker {{ font: 500 12px/1 var(--f-mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
h1 {{ font-size: clamp(30px, 5vw, 44px); font-weight: 700; margin-top: 8px; line-height: 1.1; }}
.lede {{ max-width: 68ch; color: var(--muted); margin: 12px 0 0; }}
.notice {{ margin-top: 16px; border: 1px solid var(--accent); border-left-width: 4px; padding: 12px 16px; max-width: 80ch; background: var(--card); }}
.notice b {{ color: var(--accent); }} .notice ul {{ margin: 6px 0 0; padding-left: 18px; font-size: 15px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 12px; margin-top: 16px; font-size: 14px; color: var(--muted); align-items: center; }}
nav.toc {{ margin-top: 28px; border-top: 2px solid var(--ink); padding-top: 16px; }}
nav.toc > ol {{ list-style: none; padding: 0; margin: 12px 0 0; columns: 2 300px; column-gap: 32px; }}
nav.toc > ol > li {{ break-inside: avoid; margin-bottom: 14px; }}
nav.toc > ol > li > a {{ font: 600 15px var(--f-display); text-transform: uppercase; letter-spacing: .04em; color: var(--ink); text-decoration: none; }}
nav.toc ol ol {{ list-style: none; padding: 0; margin: 4px 0 0; }}
nav.toc ol ol a {{ display: flex; gap: 8px; font-size: 14px; color: var(--ink); text-decoration: none; padding: 2px 0; }}
nav.toc .num {{ font: 500 12px/1.6 var(--f-mono); color: var(--muted); min-width: 22px; font-variant-numeric: tabular-nums; }}
.sec {{ margin-top: 48px; }}
.sec h2 {{ font-size: 26px; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; border-bottom: 3px solid var(--ink); padding-bottom: 6px; }}
.sec-intro {{ max-width: 80ch; color: var(--muted); margin: 10px 0 20px; font-size: 15px; }}
.race {{ border: 1.5px solid var(--ink); background: var(--card); margin-top: 24px; break-inside: avoid-page; }}
.race-head {{ display: flex; gap: 14px; align-items: center; background: var(--band); color: var(--band-fg); padding: 10px 16px; }}
.race-head .num {{ font: 500 14px var(--f-mono); border: 1px solid currentColor; min-width: 34px; text-align: center; padding: 3px 4px; }}
.race-head h3 {{ font-size: 21px; font-weight: 600; }}
.race-head .meta {{ margin: 2px 0 0; font: 500 11px var(--f-mono); letter-spacing: .06em; text-transform: uppercase; opacity: .78; }}
.office {{ margin: 0; padding: 10px 16px; background: var(--soft); font-size: 14.5px; border-bottom: 1px solid var(--rule); }}
.info {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); border-bottom: 1px solid var(--rule); }}
.ib {{ padding: 10px 16px 12px; min-width: 0; }} .ib + .ib {{ border-left: 1px solid var(--rule); }}
.ib-t {{ margin: 0 0 8px; font: 600 12px var(--f-display); text-transform: uppercase; letter-spacing: .06em; }}
.ib-t span {{ font: 400 12px var(--f-body); text-transform: none; letter-spacing: 0; color: var(--muted); margin-left: 6px; }}
.bar-row {{ display: grid; grid-template-columns: minmax(0, 9.5em) 1fr auto; gap: 8px; align-items: center; font-size: 13px; margin-bottom: 5px; }}
.bn {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.bv {{ font: 500 12px var(--f-mono); font-variant-numeric: tabular-nums; text-align: right; min-width: 3.5em; }}
.track {{ height: 12px; background: var(--soft); display: flex; overflow: hidden; }}
.fill {{ display: block; height: 100%; background: currentColor; }} .seg {{ display: block; height: 100%; }}
.seg.neu {{ background: var(--neu); }} .seg.neg {{ background: var(--neg); }}
.none {{ margin: 0; font-size: 13px; color: var(--muted); font-style: italic; }}
.key {{ margin: 6px 0 0; font-size: 11.5px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: center; }}
.k {{ display: inline-block; width: 10px; height: 10px; margin-right: 3px; }}
.k.rec {{ background: linear-gradient(90deg, var(--rep) 50%, var(--dem) 50%); }} .k.neu {{ background: var(--neu); }} .k.neg {{ background: var(--neg); }}
.k.sk {{ background: var(--soft); outline: 1px solid var(--rule); }}
.cands {{ display: grid; }} .cands.c2 {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
.cand {{ padding: 14px 16px 12px; border-top: 1px solid var(--rule); min-width: 0; }}
.cands.c2 > .cand:nth-child(odd) {{ border-right: 1px solid var(--rule); }}
.cands.c2 > .cand:nth-child(-n+2) {{ border-top: 0; }}
.cands.c2 > .cand:last-child:nth-child(odd) {{ grid-column: 1 / -1; border-right: 0; }}
.cand-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
.cand h4 {{ font-size: 18px; font-weight: 600; }}
.tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
.party, .tag, .lean {{ font: 500 11px/1 var(--f-mono); letter-spacing: .06em; padding: 4px 6px; border: 1px solid currentColor; white-space: nowrap; }}
.rep {{ color: var(--rep); }} .dem {{ color: var(--dem); }} .lib {{ color: var(--lib); }} .grn {{ color: var(--grn); }} .oth {{ color: var(--oth); }} .np {{ color: var(--np); }}
.tag, .muted {{ color: var(--muted); text-transform: uppercase; }} .tag.thin {{ color: var(--accent); }}
.cand ul {{ margin: 8px 0 0; padding-left: 18px; font-size: 14.5px; }} .cand li {{ margin-bottom: 4px; }}
.links {{ margin: 8px 0 0; display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 13.5px; }}
.race-links {{ padding: 8px 16px 12px; border-top: 1px solid var(--rule); margin: 0; }}
.unc-row {{ display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; margin-top: 10px; padding: 8px 16px; border: 1px dashed var(--rule); background: var(--card); font-size: 14.5px; break-inside: avoid; }}
.unc-row .num {{ font: 500 12px var(--f-mono); color: var(--muted); border: 1px solid var(--rule); min-width: 30px; text-align: center; padding: 2px 4px; }}
.uo-office {{ font-weight: 600; }} .uo-name {{ display: inline-flex; gap: 6px; align-items: baseline; }}
.uo-tag {{ margin-left: auto; font: 500 11px var(--f-mono); text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
.rng {{ font: 500 .6em var(--f-mono); color: var(--muted); vertical-align: middle; }}
nav.toc .toc-unc a {{ color: var(--muted); }}
.notice.qc {{ border-color: var(--grn); }} .notice.qc b {{ color: var(--grn); }}
.notice.qc.warn {{ border-color: var(--rep); }} .notice.qc.warn b {{ color: var(--rep); }}
.split-body {{ padding: 12px 16px 14px; }} .timeline {{ margin: 0 0 12px; padding-left: 18px; font-size: 14.5px; }}
.timeline li {{ margin-bottom: 6px; }} .stance td:first-child {{ font-weight: 600; }}
.note {{ font-size: 14px; margin: 10px 0 0; padding: 8px 12px; background: var(--soft); }}
.tablewrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14.5px; }}
th, td {{ text-align: left; vertical-align: top; padding: 8px 10px; border-bottom: 1px solid var(--rule); }}
th {{ font: 600 13px var(--f-display); text-transform: uppercase; letter-spacing: .05em; background: var(--soft); }}
.resources {{ margin-top: 48px; border-top: 3px solid var(--ink); padding-top: 12px; }}
.resources h2 {{ font-size: 22px; text-transform: uppercase; }}
.resources ul {{ columns: 2 300px; column-gap: 32px; font-size: 14.5px; padding-left: 18px; }}
.caveats {{ font-size: 13.5px; color: var(--muted); max-width: 80ch; }}
@media (max-width: 640px) {{
  .cands.c2, .info {{ grid-template-columns: 1fr; }}
  .cands.c2 > .cand:nth-child(odd) {{ border-right: 0; }}
  .cands.c2 > .cand:nth-child(2) {{ border-top: 1px solid var(--rule); }}
  .ib + .ib {{ border-left: 0; border-top: 1px solid var(--rule); }}
}}
@media print {{
  :root {{ --paper: #fff; --card: #fff; }} body {{ font-size: 10.5pt; }} .wrap {{ max-width: none; padding: 0; }}
  .race {{ break-inside: avoid; }} .sec h2 {{ break-after: avoid; }} .sec {{ break-before: page; margin-top: 0; }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} a {{ text-decoration: none; }}
}}
</style>
<div class="wrap">
  <p class="kicker">{E(sub)}</p>
  <h1>{E(title)}</h1>
  <p class="lede">Every contest on this ballot, in exact ballot order. Contest numbers match the ballot cheat sheet. Contested races get a full box; uncontested races are one line in their ballot position. This guide is nonpartisan and recommends no candidate or vote.</p>
  {vi_html}
  {qc_html}
  <div class="legend"><span class="party rep">REP</span><span class="party dem">DEM</span><span class="party lib">LIB</span><span class="party grn">GRN</span><span class="party oth">Other / Ind.</span><span class="party np">Nonpartisan</span><span class="tag">Incumbent</span><span class="tag thin">Little info</span></div>
  <nav class="toc" aria-label="Races"><p class="kicker">Contents</p><ol>{"".join(toc)}</ol></nav>
  {"".join(body)}
  <section class="resources"><h2>Resources</h2><ul>{res}</ul>
  <p class="caveats"><b>Caveats.</b> {E(data.get("caveats", ""))} Compiled {E(el.get("compiled", ""))}.</p></section>
</div>
'''


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build the research guide from ballot.json")
    ap.add_argument("ballot_json")
    ap.add_argument("out_html", help="artifact page (fragment) to publish")
    ap.add_argument("--standalone", metavar="FILE.html",
                    help="also write a complete, self-contained HTML file for download/email/offline reading")
    a = ap.parse_args()
    page = build(load(a.ballot_json))
    open(a.out_html, "w").write(page)
    print("wrote", a.out_html)
    if a.standalone:
        open(a.standalone, "w").write(standalone(page))
        print("wrote", a.standalone)
