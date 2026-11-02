#!/usr/bin/env python3
"""Regression tests for verify_ballot.py's PDF reader, using real sample ballots.

For each fixture in tests/fixtures/manifest.json:
  1. Read the ballot PDF with the given --columns setting and compare the reading order, line by
     line, to the saved golden file (fixtures/<name>.lines.txt). Any change is reported as a diff.
  2. If the fixture has a names-only ballot.json, run the full ballot-match check on it
     and require 0 errors.

Usage:
  python tests/run_regression.py            # run all fixtures; exit 1 on any failure
  python tests/run_regression.py --update   # rewrite the golden files after an intended change
                                            # (review the diff with `git diff tests/` before committing)

Requires pdfplumber (pip install pdfplumber).
"""
import argparse
import difflib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
SCRIPTS = os.path.join(HERE, "..", "ballot-research-guide", "scripts")
sys.path.insert(0, SCRIPTS)
import verify_ballot  # noqa: E402


def lines_for(fx):
    pdf = os.path.join(FIX, fx["pdf"])
    return [f"p{p}: {t}" for p, t in verify_ballot.ballot_lines(pdf, str(fx["columns"]))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="rewrite golden reading-order files")
    args = ap.parse_args()
    fixtures = json.load(open(os.path.join(FIX, "manifest.json")))["fixtures"]
    failed = 0
    for fx in fixtures:
        name = fx["name"]
        golden = os.path.join(FIX, f"{name}.lines.txt")
        got = lines_for(fx)
        if args.update:
            with open(golden, "w") as f:
                f.write("\n".join(got) + "\n")
            print(f"updated  {name}: {len(got)} lines")
            continue
        want = open(golden).read().splitlines()
        if got == want:
            print(f"PASS     {name}: reading order matches golden ({len(got)} lines, --columns {fx['columns']})")
        else:
            failed += 1
            print(f"FAIL     {name}: reading order changed (--columns {fx['columns']})")
            for d in list(difflib.unified_diff(want, got, "golden", "now", lineterm="", n=0))[:40]:
                print("         " + d)
        if fx.get("ballot_json"):
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "verify_ballot.py"),
                 "--pdf", os.path.join(FIX, fx["pdf"]), "--json", os.path.join(FIX, fx["ballot_json"]),
                 "--columns", str(fx["columns"]), "--report", os.devnull],
                capture_output=True, text=True)
            head = (r.stdout.strip().splitlines() or ["(no output)"])[0]
            if r.returncode == 0:
                print(f"PASS     {name}: ballot match, {head}")
            else:
                failed += 1
                print(f"FAIL     {name}: ballot match, {head}")
                for ln in r.stdout.splitlines()[1:15]:
                    print("         " + ln)
    if args.update:
        return 0
    print(f"\nAll {len(fixtures)} fixtures passed" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
