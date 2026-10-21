---
name: ballot-research-guide
description: Turn a voter's sample ballot (any U.S. state, county or city) into a nonpartisan research guide (web page + PDF) and a one-page fill-in ballot cheat sheet, with state-specific first-time-voter rules and voting windows. Also helps the voter find their sample ballot.
---

# Ballot Research Guide

Produce two deliverables from a voter's sample ballot:

1. **Research guide.** Every contested race in ballot order. Each race is a clearly separated box with a poll strip, candidate facts and links. Published as an artifact and rendered to PDF.
2. **Cheat sheet.** One printable letter page listing **every** contest, contested and uncontested, in exact ballot order, with checkboxes the voter fills in before going to vote.

Both are built from one data file, `ballot.json`, by the scripts in `scripts/`. Gather the facts, write the JSON, run the scripts.

## Ground rules (apply throughout)

- **Strictly nonpartisan.** Never recommend a candidate or a vote on a measure, even if the user shares their own leanings. Give every side the same effort, tone and depth.
- **Verify, don't recall.** Election rules, dates, deadlines and candidate facts change. Look up everything about this election; never fill a gap from memory.
- **No voter-file data.** Never use voter registration or primary-voting history to label anyone.
- **Copyright.** Paraphrase sources. Keep any quote under 15 words, and use at most one quote per source.
- **Flag thin information.** When little is published about a candidate, say so. Never pad with guesses.

## Step 1: Get the ballot

- **If the user attached a sample ballot** (PDF or images), read every page.
- **If not, help them find it.**
  - Ask for state and county. Ask for city, or address or precinct, only if they're comfortable sharing it.
  - Search for the county (or city or town, in states that run elections locally) elections office's sample ballot or "my ballot" lookup.
  - Give them the exact page, plus VOTE411.org and Ballotpedia's sample-ballot lookup as alternatives.
  - Ask them to download and attach the PDF.
  - Never reconstruct a ballot from an address. Ballots vary by precinct.
- **Transcribe into `ballot.json`.** Record every contest in exact order, including uncontested races, write-in lines, retention questions, measures and propositions. Keep the ballot's page or column labels and its section headers (federal, state, county, city, school district, special district, measures).
- **Confirm the transcription.** Count the contests and tell the user the count so they can check it against their ballot.

## Step 2: Ask a few questions

Use **one** AskUserQuestion call with at most 4 questions, asking only what changes the output.

- **Scope.** Research every contested race, or skip races the user has already decided? Default to all, and say why: guides often get shared, for example with a first-time voter.
- **Key local issues.** Which local controversies should each candidate's stance be documented on?
  - First run 2–3 quick news searches on the jurisdictions on this ballot.
  - Offer real issues as options, such as a school-district split, a bond, annexation, a rezoning or a recall.
- **Audience.** Is the guide for the user, or also for someone else? If a first-time voter will use it, include the full "First time voting?" box. Include a short version either way.
- **Party signals.** Should public party signals be noted for nonpartisan candidates?

**If the user isn't around to answer:** include all contested races, add the short voting-rules box, skip the issue section, and say which defaults you chose.

## Step 3: Verify the state and local voting rules

Read `references/state-voting-rules.md`. It lists every rule to verify and the sources to check, in priority order.

- Fill the `voting_info` block in `ballot.json` from this election's official sources: the state election office and the county or city clerk.
- Rules differ sharply by state: photo ID vs. no ID, same-day registration, early-voting dates, vote centers vs. assigned polling places, all-mail states, straight-ticket voting, phones and notes in the booth, ranked-choice voting, and ballot-return deadlines.
- Cite the official source for each item.
- If a rule can't be confirmed, write "Check with [office]" rather than guessing.

## Step 4: Research

For breadth, use a research subagent or extended research. Brief it with the full contest list, the issues from Step 2 and the rules below. Then fill gaps with targeted searches.

**For every contested race:**

- **Office.** One plain-language line on what the office does. Explain anything obscure or misleadingly named, such as a Railroad Commission, a soil and water district, or a coroner.
- **Candidates.**
  - Background, incumbency, and platform or key positions.
  - Notable endorsements from across the spectrum.
  - Money raised, where reported.
  - Documented controversies, from credible outlets only.
  - Links: campaign site, Facebook, Ballotpedia, VOTE411, and local news Q&As.
- **Voter polls.**
  - Use the latest public polls, with pollster, dates and margin of error.
  - Prefer nonpartisan or academic pollsters, and label partisan or internal polls.
  - With no poll, say so. A recent actual result between the same candidates may be shown, labeled as a result.
- **Judges.**
  - Include state and local bar association polls or ratings, with date, response rate and method. Say they are lawyer surveys, not endorsements.
  - Retention elections: include the state's judicial performance evaluation if one exists.
  - Include newspaper endorsements from more than one outlet.
- **Local issue stances** (from Step 2).
  - Gather on-record statements, votes and past roles.
  - Order candidates from most open to least open on the issue only when the record supports it.
  - If no candidate holds a position the user might expect, say so plainly.
- **Party signals** (nonpartisan races only, if requested).
  - Use only public party offices, partisan-group endorsements or recommendations, and candidates' own statements.
  - Write "none found" otherwise, and note that this doesn't mean they have no affiliation.
- **Measures, bonds and propositions.**
  - Give a neutral summary, the sponsor's rationale, and organized support and opposition.
  - Give the fiscal or tax impact with its assumptions, and quote the official ballot language if short.
  - Note supermajority thresholds where they apply.
- **Sources.** Prefer original and local sources: election offices, local and statewide newsrooms, Ballotpedia. Treat partisan-leaning outlets as single-source and label them.

## Step 5: Write ballot.json and build

- The schema and a small worked example are in `assets/example-ballot.json`. Follow it exactly.
- Party values are free text. The scripts map common labels (REP/R/Republican, DEM/D/Democratic, LIB, GRN, IND, nonpartisan) to colors: **Republicans red, Democrats blue, Libertarians gold, Greens green, independents and other parties purple, nonpartisan slate.**

```bash
pip install playwright --break-system-packages -q && python -m playwright install chromium   # once, if missing
python scripts/build_guide.py ballot.json guide.html          # research guide (HTML)
python scripts/build_cheatsheet.py ballot.json cheatsheet.html
python scripts/render_pdf.py guide.html guide.pdf --footer "Ballot Guide"
python scripts/render_pdf.py cheatsheet.html cheatsheet.pdf --one-page
```

**What the guide includes:**
- A header and a voting-rules box.
- A contents list.
- One ruled box per contested race. Each box has a header band, an office line and a **poll strip**: voter poll bars plus, for judges, bar-poll bars. Rating-style bar polls show as stacked bars, and missing data says so.
- Side-by-side candidate cards.
- Optional issue sections placed before the related races, with a timeline and a stance table that includes a party-signal column.
- A measures table, resources and caveats.

**What the cheat sheet includes:**
- Every contest, numbered, with divider bars at each ballot page or section change.
- A checkbox per choice; "unopposed" tags; write-in lines; For/Against or Yes/No boxes on measures.
- Ranked-choice contests get a rank grid. The voting-rules reminder sits at the top.
- `--one-page` shrinks the type until it fits one letter page. **If it still won't fit** (very long ballots), set `"cheatsheet_two_sided": true` and print double-sided.

**Before publishing:**
- Render two or three guide pages and the cheat sheet to PNG with `pdftoppm` and look at them once.
- Fix anything clipped or overlapping.
- The cheat-sheet order must match the ballot exactly.

## Step 6: Deliver

- Before publishing, load the `artifact-design` skill. Then publish `guide.html` as an artifact and send both PDFs.
- Tell the user, in one line each:
  - The artifact is private until they share it from the page's Share menu.
  - The cheat sheet is for marking in pen and bringing to vote, where phones may be restricted (say what this state's rule is).
- Offer one next step at most: a scheduled recheck of polls and late news a few days before Election Day, or before the last day of early voting if the state has one. If they accept, create it as a scheduled task that updates the same artifact.
