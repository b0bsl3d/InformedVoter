# Changelog

## 2026-11-02: Regression suite with real ballots

- `tests/fixtures/` holds two official sample ballots:
  - `tarrant-tx-3471-127.pdf`: Tarrant County, TX, precinct 3471-127.
  - `carver-mn-victoria-p4.pdf`: Carver County, MN, City of Victoria P4. It comes with a names-only `ballot.json` (35 contests, no research content).
- `tests/run_regression.py` compares each ballot's reading order with a saved golden file and runs the full ballot-match check on the Carver transcription. `--update` rewrites the golden files after an intended change.
- The Tarrant golden file is identical to the reading-order dump in `examples/tarrant-county-tx-2026/qc-report.md`, so it anchors the run that passed 126/126.
- Run against the pre-fix checker (`7c23c5e`), the suite fails on the Carver ballot, so it would have caught this bug.

## 2026-11-02: Ballot checker reads mixed-column ballots

Found while building a guide for a Carver County, Minnesota ballot (City of Victoria P4). The front has three columns and the back has two. `verify_ballot.py` reported every contest in the later columns as out of order, even though the transcription was correct.

**Two causes**

1. **One column count for the whole PDF.** `--columns` applied the same number to every page. So no single value could read both the three-column front and the two-column back.
2. **Centered headers hid the real gap.** The column finder looks for the emptiest vertical band in the middle 60% of the page. Centered titles and the "Instructions to Voters" line cross the real gap between columns, so that gap never reads as fully empty. On the back, the two judicial columns fill only the left two-thirds of the page, so the empty margin beside the second column won instead. The cut landed outside the text and the page was read as one column.

**Fixes** (`ballot-research-guide/scripts/verify_ballot.py`)

- **Per-page column counts.** `--columns` now accepts a comma-separated list with one count per page, such as `--columns 3,2`. The last value repeats for any later pages. A single number works as before.
- **Better gap detection.** A cut must now leave real text on each side, within the stretch between cuts already made: at least 8 words or 2% of the page's words, whichever is more. A stray footer or the end of an instruction line no longer counts. Among the cuts that qualify, the finder picks the emptiest band nearest the page center, as before. If no position qualifies, the old rule applies.

  A first version picked whichever near-empty band split the words most evenly. That cut through headers on the Tarrant County ballot, whose columns are uneven, so it was replaced the same day (it shipped briefly in 5558bc6; use 040d617 or later).

**Testing**

- **Carver County ballot.** `--columns 3,2` (and plain `--columns 3`) now pass with 0 errors across all 35 contests. Before the fix, 8–28 contests failed depending on the setting.
- **Regression on the Tarrant County example (precinct 3471-127).** With the default `--columns 2`, the new reader produces exactly the same reading order as the previous version, line for line on all 6 pages. It also matches the dump in `examples/tarrant-county-tx-2026/qc-report.md`, the run that passed 126/126 names in order. That ballot has a short right column on page 5 (18 words); it still splits correctly.
- **Synthetic layouts**, all split correctly:
  - two equal columns with a centered header;
  - three equal columns with a centered header;
  - two columns in the left two-thirds of the page;
  - two unequal columns;
  - two columns with no header;
  - a very short right column.

**Docs.** `SKILL.md`, both READMEs and `dist/ballot-research-guide.zip` are updated.
