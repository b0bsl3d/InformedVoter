# Ballot Research Guide: a Claude skill

Give Claude your sample ballot from any U.S. state, county or city. It produces two things:

- **A research guide.** Every contested race in ballot order, one box per race. Each box has a voter-poll strip, a bar-poll strip for judges, candidate backgrounds, positions and links, and stances on local issues you name. You get it as a shareable web page and a PDF.
- **A one-page cheat sheet.** Every contest on your ballot, including uncontested ones, in ballot order with checkboxes. Mark it in pen and bring it to vote.

The guide also opens with your state's voting rules for this election: ID, early-voting dates, Election Day hours, straight-ticket rules, and whether phones and notes are allowed. There's a fuller version for first-time voters. Claude verifies these against official state and county sources every time.

The guide is strictly nonpartisan: no recommendations. Party colors: Republicans red, Democrats blue, Libertarians gold, Greens green, independents and other parties purple, nonpartisan slate.

## Install

1. Zip the `ballot-research-guide` folder, or use the provided zip.
2. In Claude, go to **Customize → Skills → + → Create skill → Upload a skill**, and choose the zip.

## Use

Say something like:

- "Here's my sample ballot. Build me a voter guide and cheat sheet." Then attach the PDF.
- "Help me find my sample ballot for Maricopa County, Arizona, and then build the guide."

Claude asks up to four quick questions: which races, which local issues, who the guide is for, and whether to note party signals for nonpartisan races. Then it does the research and delivers both files.

## Contents

- `SKILL.md`: the workflow Claude follows.
- `references/state-voting-rules.md`: the checklist and source order for verifying state and local voting rules.
- `scripts/build_guide.py`: builds the guide HTML from `ballot.json`.
- `scripts/build_cheatsheet.py`: builds the cheat sheet. It handles write-ins, "vote for N" contests, ranked-choice grids and measures.
- `scripts/render_pdf.py`: renders HTML to PDF with headless Chromium. `--one-page` auto-fits the cheat sheet.
- `assets/example-ballot.json`: a data-file example with fictional candidates.

Requires Python 3 and Playwright (`pip install playwright && python -m playwright install chromium`).
