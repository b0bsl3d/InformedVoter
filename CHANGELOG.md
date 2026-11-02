# Changelog

## 2026-11-02: Ballot checker reads mixed-column ballots

Found while building a guide for a Carver County, Minnesota ballot (City of Victoria P4). The front has three columns and the back has two. `verify_ballot.py` reported every contest in the later columns as out of order, even though the transcription was correct.

**Two causes**

1. **One column count for the whole PDF.** `--columns` applied the same number to every page. So no single value could read both the three-column front and the two-column back.
2. **Centered headers hid the real gap.** The column finder looks for the emptiest vertical band in the middle 60% of the page. Centered titles and the "Instructions to Voters" line cross the real gap between columns, so that gap never reads as fully empty. On the back, the two judicial columns fill only the left two-thirds of the page, so the empty margin beside the second column won instead. The cut landed outside the text and the page was read as one column.

**Fixes** (`ballot-research-guide/scripts/verify_ballot.py`)

- **Per-page column counts.** `--columns` now accepts a comma-separated list with one count per page, such as `--columns 3,2`. The last value repeats for any later pages. A single number works as before.
- **Better gap detection.** Any nearly empty band now counts as a possible gap: coverage up to 3 words, or 10% of the busiest column. Among those, the finder picks the cut that best splits the words into even column boundaries. A margin with nothing to its right no longer wins. If no band qualifies, the old rule applies.

**Testing**

- Carver County ballot: `--columns 3,2` (and plain `--columns 3`) now pass with 0 errors across all 35 contests. Before the fix, 8–28 contests failed depending on the setting.
- Synthetic layouts, all split correctly:
  - two equal columns with a centered header;
  - three equal columns with a centered header;
  - two columns in the left two-thirds of the page;
  - two unequal columns;
  - two columns with no header.

**Docs.** `SKILL.md`, both READMEs and `dist/ballot-research-guide.zip` are updated.
