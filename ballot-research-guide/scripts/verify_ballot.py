#!/usr/bin/env python3
"""Quality gate: verify ballot.json (and the built guide / cheat sheet) against the official ballot PDF.

Usage:
  python verify_ballot.py --pdf ballot.pdf --json ballot.json \
      [--html guide.html] [--html cheatsheet.html] [--columns 2] [--report qc_report.md]

Checks (ERROR = must fix before delivering; WARN = review by hand):
  1. Every candidate name in ballot.json appears on the ballot PDF            (ERROR: possible hallucination/misspelling)
  2. Contests and candidates appear in the same order as on the ballot      (ERROR: out of order)
  3. Candidate-looking lines on the ballot that ballot.json is missing      (WARN: possible omitted contest/candidate)
  4. Write-in lines and measure choices match the ballot counts             (WARN)
  5. Each HTML output numbers contests 1..N in ballot order, and each
     numbered contest lists exactly the candidates ballot.json has for it  (ERROR: numbering/content mismatch)
  6. Research hygiene: every non-"thin" candidate has at least one source
     link; every poll and bar poll has a source label                       (WARN)

Exit code 1 if any ERROR, so it can gate delivery.

Reading order: each page is split into columns at the widest empty vertical band(s) and read
top-to-bottom, left column first (how U.S. multi-column ballots are read). Use --columns 1 for
single-column ballots or if detection misbehaves; check the "page text" dump in the report.
"""
import argparse
import html as htmlmod
import json
import re
import sys
import unicodedata

try:
    import pdfplumber
except ImportError:
    sys.exit("pip install pdfplumber --break-system-packages")

PARTY_TOKENS = {"REP", "DEM", "LIB", "GRN", "IND", "R", "D", "L", "G", "NPP", "WFP", "CON", "REF"}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[\"'“”‘’`´]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def split_columns(words, width, ncols):
    if ncols == 1 or not words:
        return [words]
    # coverage histogram (1pt buckets) using body words only (skip full-width header rows)
    cov = [0] * (int(width) + 2)
    for w in words:
        for x in range(int(w["x0"]), int(w["x1"]) + 1):
            cov[x] += 1
    lo, hi = int(width * 0.2), int(width * 0.8)
    cuts = []
    for _ in range(ncols - 1):
        best = min(range(lo, hi), key=lambda x: (cov[x], abs(x - width / 2)))
        cuts.append(best)
        for x in range(max(lo, best - 40), min(hi, best + 40)):
            cov[x] = 10 ** 9  # do not pick a neighbour as the next cut
    cuts.sort()
    cols = [[] for _ in range(len(cuts) + 1)]
    for w in words:
        i = sum(1 for c in cuts if w["x0"] >= c)
        cols[i].append(w)
    return cols


def ballot_lines(pdf_path, ncols):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            # Drop watermark text ("SAMPLE BALLOT" stamps): rotated or much larger than body text.
            sizes = sorted(round(c.get("size", 0), 1) for c in page.chars if c.get("upright", True))
            body = sizes[len(sizes) // 2] if sizes else 10
            clean = page.filter(lambda o: o.get("object_type") != "char"
                                or (o.get("upright", True) and o.get("size", 0) <= body * 1.8
                                    and not (o.get("non_stroking_color") in ((0.8,), (0.9,), [0.8], [0.9]))))
            words = clean.extract_words(keep_blank_chars=False, use_text_flow=False)
            for col in split_columns(words, page.width, ncols):
                rows = {}
                for w in sorted(col, key=lambda w: (round(w["top"] / 3), w["x0"])):
                    rows.setdefault(round(w["top"] / 3), []).append(w["text"])
                for k in sorted(rows):
                    lines.append((pno, " ".join(rows[k])))
    return lines


def contests_from_json(data):
    out = []
    for s in data["sections"]:
        for c in s["contests"]:
            out.append(c)
    return out


def check(args):
    data = json.load(open(args.json))
    contests = contests_from_json(data)
    lines = ballot_lines(args.pdf, args.columns) if args.pdf else []
    stream = " | ".join(norm(t) for _, t in lines)
    errors, warns, info = [], [], []

    if not args.pdf:
        warns.append("No ballot PDF given: names and order were NOT checked against the official ballot")
    # 1 + 2: names present and in order
    cursor = 0
    matched_names = set()
    total_names = 0
    for n, c in enumerate(contests, 1):
        if not args.pdf:
            total_names += len(c.get("candidates", []))
            continue
        if c.get("type") == "measure":
            # measures: look for a distinctive key (e.g. "proposition a"); warn only
            pos = stream.find(norm(c.get("ballot_key", "")), cursor) if c.get("ballot_key") else -1
            if c.get("ballot_key"):
                if pos < 0:
                    errors.append(f"#{n} {c['office']}: ballot_key '{c['ballot_key']}' not found after previous contest (missing or out of order)")
                else:
                    cursor = pos
            continue
        for x in c.get("candidates", []):
            total_names += 1
            nm = norm(x["name"])
            pos = stream.find(nm, cursor)
            if pos >= 0:
                cursor = pos + len(nm)
                matched_names.add(nm)
                continue
            anywhere = stream.find(nm)
            if anywhere >= 0:
                errors.append(f"#{n} {c['office']}: '{x['name']}' is on the ballot but OUT OF ORDER (appears earlier than the previous contest)")
            else:
                # try last name only to distinguish misspelling from hallucination
                last = nm.split()[-1] if nm else ""
                hint = " (last name found; likely spelling/nickname difference)" if last and f" {last}" in f" {stream}" else " (NOT FOUND: possible hallucination)"
                errors.append(f"#{n} {c['office']}: '{x['name']}' not found on ballot{hint}")

    # 3: candidate-looking lines on the ballot not in JSON
    OFFICE_WORDS = re.compile(r"\b(proposition|district|court|place|precinct|measure|amendment|question|legend|party|senator|representative|judge|justice|commissioner|clerk|attorney|governor|trustee|board)\b", re.I)

    def party_only(t):
        toks = t.split()
        if not toks or len(toks) > 2:
            return False
        for tk in toks:
            m2 = re.fullmatch(r"([A-Z]{1,4})\1?", tk)
            if not (m2 and m2.group(1) in PARTY_TOKENS):
                return False
        return True

    def is_known(name_line):
        nm = norm(name_line)
        return bool(nm) and any(nm == m or nm in m or m in nm for m in matched_names)

    def namey(t):
        toks = t.split()
        return 2 <= len(toks) <= 6 and not OFFICE_WORDS.search(t) and not party_only(t) and "=" not in t

    flagged = set()
    for i, (pno, t) in enumerate(lines):
        toks = t.split()
        if toks:
            m2 = re.fullmatch(r"([A-Z]{1,4})\1?", toks[-1])
            if m2 and m2.group(1) in PARTY_TOKENS and len(toks) >= 3 and namey(" ".join(toks[:-1])):
                if not is_known(" ".join(toks[:-1])) and t not in flagged:
                    flagged.add(t)
                    warns.append(f"Ballot page {pno}: '{t}' looks like a candidate line but is not in ballot.json")
                continue
        if party_only(t):
            neigh = [lines[j] for j in (i - 1, i + 1) if 0 <= j < len(lines) and lines[j][0] == pno and namey(lines[j][1])]
            if neigh and not any(is_known(x[1]) for x in neigh):
                cand = neigh[-1][1]
                if cand not in flagged:
                    flagged.add(cand)
                    warns.append(f"Ballot page {pno}: '{cand}' (party {t}) looks like a candidate but is not in ballot.json")

    # 4: write-ins and measures
    wi_pdf = sum(1 for _, t in lines if re.search(r"\bwrite[- ]?in\b", t, re.I))
    wi_json = sum(1 for c in contests if c.get("writein"))
    if args.pdf and wi_pdf != wi_json:
        warns.append(f"Write-in lines: ballot shows {wi_pdf}, ballot.json flags {wi_json}")
    meas_json = sum(1 for c in contests if c.get("type") == "measure")
    meas_pdf = sum(1 for _, t in lines if re.match(r"^(for|yes)\b", t.strip(), re.I))
    if args.pdf and meas_json and meas_pdf != meas_json:
        warns.append(f"Measures: ballot shows about {meas_pdf} For/Yes choice lines, ballot.json has {meas_json} measures")

    # 5: built outputs
    for path in args.html or []:
        h = open(path).read()
        blocks = re.findall(r'data-contest="([0-9]+)(?:-([0-9]+))?"', h)
        nums = []
        for a, b in blocks:
            nums.extend(range(int(a), int(b or a) + 1))
        expect = list(range(1, len(contests) + 1))
        if nums != expect:
            missing = sorted(set(expect) - set(nums))
            extra = sorted(set(nums) - set(expect))
            dup = sorted({x for x in nums if nums.count(x) > 1})
            out_of_order = nums != sorted(nums)
            errors.append(f"{path}: contest numbering wrong (missing {missing[:10]}, extra {extra[:10]}, duplicates {dup[:10]}, out_of_order={out_of_order})")
        # candidate sets per contest
        parts = re.split(r'(?=data-contest=")', h)
        for part in parts[1:]:
            m = re.match(r'data-contest="([0-9]+)(?:-([0-9]+))?"', part)
            a = int(m.group(1))
            if m.group(2):
                continue  # grouped measures block
            if a > len(contests):
                continue
            c = contests[a - 1]
            if c.get("type") == "measure":
                continue
            got = [htmlmod.unescape(x) for x in re.findall(r'data-cand="([^"]*)"', part)]
            want = [x["name"] for x in c.get("candidates", [])]
            if [norm(g) for g in got] != [norm(w) for w in want]:
                errors.append(f"{path}: #{a} {c['office']} lists {got} but ballot.json has {want}")

    # 6: research hygiene
    for n, c in enumerate(contests, 1):
        if c.get("type") == "measure":
            continue
        if len(c.get("candidates", [])) > 1:
            for x in c["candidates"]:
                if not x.get("thin") and not x.get("links") and not c.get("links"):
                    warns.append(f"#{n} {c['office']}: '{x['name']}' has facts but no source link")
        for k in ("poll", "bar_poll"):
            if c.get(k) and not c[k].get("source"):
                warns.append(f"#{n} {c['office']}: {k} has no source label")

    info.append(f"Contests in ballot.json: {len(contests)}")
    if args.pdf:
        bad = sum(1 for e in errors if "not found" in e or "OUT OF ORDER" in e)
        info.append(f"Candidate names checked against ballot PDF: {total_names - bad}/{total_names} found in order")
    return errors, warns, info, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="official sample ballot PDF (strongly recommended)")
    ap.add_argument("--json", required=True)
    ap.add_argument("--html", action="append")
    ap.add_argument("--columns", type=int, default=2)
    ap.add_argument("--report", default="qc_report.md")
    args = ap.parse_args()
    errors, warns, info, lines = check(args)
    status = "FAIL" if errors else "PASS"
    rep = [f"# Ballot QC report: {status}", ""] + [f"- {i}" for i in info] + [""]
    rep += ["## Errors (must fix)", ""] + ([f"- {e}" for e in errors] or ["- none"]) + [""]
    rep += ["## Warnings (review)", ""] + ([f"- {w}" for w in warns] or ["- none"]) + [""]
    rep += ["## Ballot text in reading order (for spot checks)", "", "```"] + [f"p{p}: {t}" for p, t in lines] + ["```"]
    open(args.report, "w").write("\n".join(rep))
    print(f"{status}: {len(errors)} error(s), {len(warns)} warning(s). Report: {args.report}")
    for e in errors[:25]:
        print("ERROR", e)
    for w in warns[:25]:
        print("WARN ", w)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
