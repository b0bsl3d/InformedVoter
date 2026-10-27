---
name: ballot-research-guide
description: Turn a voter's sample ballot (any U.S. state, county or city) into a nonpartisan research guide (web page + PDF) and a one-page fill-in ballot cheat sheet, with state-specific first-time-voter rules and voting windows, plus mandatory quality checks against the official ballot and sources. Also helps the voter find their sample ballot.
---

# Ballot Research Guide

Produce two deliverables from a voter's sample ballot:

1. **Research guide.** Every contest in exact ballot order. Contested races get a full box (poll strip, candidate facts, links); uncontested races get one line in their ballot position. Published as an artifact and rendered to PDF.
2. **Cheat sheet.** One printable letter page listing every contest in exact ballot order, with checkboxes to fill in before voting.

**Both outputs use the same contest numbers: the contest's position on the ballot (1..N).** Contest #17 is the same race on the ballot, in the guide and on the cheat sheet. Both are built from one file, `ballot.json`, by the scripts in `scripts/`. Nothing is delivered until the quality gates in Step 6 pass.

## Ground rules (apply throughout)

- **Strictly nonpartisan.** Never recommend a candidate or a vote on a measure, even if the user shares their own leanings. Give every side the same effort, tone and depth.
- **The ballot is the only source for what is on the ballot.**
  - Never add a contest, candidate or measure that you can't point to on the sample ballot.
  - Never fill in an uncontested race, a name or a spelling from memory or from a news story.
- **Every fact needs a source you looked at this session.**
  - No facts from memory: no bios, poll numbers, dollar amounts, dates or rules.
  - If you can't source it, leave it out or mark it "unverified".
- **No voter-file data.** Never use voter registration or primary-voting history to label anyone.
- **Copyright.** Paraphrase sources. Keep any quote under 15 words, and use at most one quote per source.
- **Flag thin information.** When little is published about a candidate, say so ("Little info"). Never pad with guesses.

## Step 1: Get the ballot

- **If the user attached a sample ballot** (PDF or images), read every page.
- **If not, help them find it.**
  - Ask for state and county. Ask for city, or address or precinct, only if they're comfortable sharing it.
  - Search for the county (or city or town, in states that run elections locally) elections office's sample ballot or "my ballot" lookup.
  - Give them the exact page, plus VOTE411.org and Ballotpedia's sample-ballot lookup as alternatives.
  - Ask them to download and attach the PDF.
  - Never reconstruct a ballot from an address: ballots vary by precinct.
  - If no PDF is possible, the guide must say plainly that it was not checked against the official ballot (Step 6).
- **Transcribe into `ballot.json`.**
  - **Reading order.** Most ballots have two or three columns per page. Read each page column by column: down the left column, then the next. Extract text with `pdftotext -layout` or pdfplumber, and look at page images (`pdftoppm -png`) to confirm the column flow.
  - **Completeness.** Record every contest in order, including uncontested races, write-in lines, retention questions, measures and propositions.
  - **Exact spelling.** Copy names exactly as printed, including middle initials and quoted nicknames (e.g., `William P. 'Bill' Brandt`).
  - **Labels.** Keep page labels and section headers.
  - **Measure keys.** For each measure, set `ballot_key` to a short phrase that appears on the ballot (e.g., `"proposition a"`).
- **Confirm the count.** Tell the user the contest count so they can check it against their ballot.

## Step 2: Ask a few questions

Use **one** AskUserQuestion call with at most 4 questions, asking only what changes the output.

- **Scope.** Research every contested race, or skip races the user has already decided? Default to all, and say why: guides often get shared, for example with a first-time voter.
  - Skipped races still appear in both outputs in their ballot position, so numbering never shifts.
- **Key local issues.** Which local controversies should each candidate's stance be documented on?
  - First run 2–3 quick news searches on the jurisdictions on this ballot.
  - Offer real issues as options, such as a school-district split, a bond, annexation, a rezoning or a recall.
- **Audience.** Is the guide for the user, or also for someone else? If a first-time voter will use it, include the full "First time voting?" box. Include a short version either way.
- **Party signals.** Should public party signals be noted for nonpartisan candidates?

**If the user isn't around to answer:** research all contested races, add the short voting-rules box, skip the issue section, and say which defaults you chose.

## Step 3: Verify the state and local voting rules

Read `references/state-voting-rules.md`. It lists every rule to verify and the sources to check, in priority order.

- Fill `voting_info` in `ballot.json` from this election's official sources: the state election office and the county or city clerk.
- Give each item a `source` URL that you fetched this session.
- If a rule can't be confirmed, write "Check with [office]" rather than guessing.
- **Check every date against a calendar, including the day of the week.** For example, "Saturday, Oct. 30" is wrong in 2026, because Oct. 30 is a Friday.

## Step 4: Research

For breadth, use a research subagent or extended research. Brief it with the contest list, the issues from Step 2 and the rules below. Then fill gaps with targeted searches. **Store the source link next to each fact** in `links` on the candidate or race.

**For every contested race:**

- **Office.** One plain-language line on what the office does. Explain anything obscure or misleadingly named, such as a Railroad Commission, a soil and water district, or a coroner.
- **Candidates.**
  - Background, incumbency, and platform or key positions.
  - Notable endorsements from across the spectrum.
  - Money raised, where reported.
  - Documented controversies, from credible outlets only.
  - Links: campaign site, Facebook, Ballotpedia, VOTE411, and local news Q&As.
- **Voter polls.**
  - Use the latest public polls, with pollster, dates and margin of error, and the source in `poll.source`.
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
  - Use only public party offices, partisan-group endorsements or recommendations, and candidates' own statements, including answers on public questionnaires such as iVoterGuide.
  - **Search every side equally.** Check both major parties' county endorsement lists, conservative and progressive group slates, and each candidate's questionnaires. A table that flags one side's endorsements but misses the other's is a quality failure.
  - Write "none found" otherwise, and note that this doesn't mean they have no affiliation.
- **Measures, bonds and propositions.**
  - Give a neutral summary, the sponsor's rationale, and organized support and opposition.
  - Give the fiscal or tax impact with its assumptions, and quote the official ballot language if short.
  - Note supermajority thresholds where they apply.
- **Sources.** Prefer original and local sources: election offices, local and statewide newsrooms, Ballotpedia. Treat partisan-leaning outlets as single-source and label them.

## Step 5: Write ballot.json and build

- The schema and a worked example are in `assets/example-ballot.json`. Follow it exactly.
- **Sections are contiguous runs of the ballot**, such as "Page 1" or "County". Never move a contest out of ballot order or regroup races by topic. The builders number contests by position, so moving one breaks the numbering for every contest after it.
- Party values are free text. The scripts map common labels to colors: **Republicans red, Democrats blue, Libertarians gold, Greens green, independents and other parties purple, nonpartisan slate.**

```bash
pip install playwright pdfplumber --break-system-packages -q && python -m playwright install chromium   # once, if missing
python scripts/build_guide.py ballot.json guide.html
python scripts/build_cheatsheet.py ballot.json cheatsheet.html
python scripts/render_pdf.py guide.html guide.pdf --footer "Ballot Guide"
python scripts/render_pdf.py cheatsheet.html cheatsheet.pdf --one-page
```

- **Cheat sheet length.** `--one-page` shrinks the type until it fits one letter page. If it still won't fit, set `"cheatsheet_two_sided": true` and print double-sided.
- **Ranked-choice contests** get a rank grid. Measures get For/Against (or Yes/No) boxes.

## Step 6: Quality gates (required; do not deliver until these pass)

Record each gate's result as one plain sentence in `ballot.json` under `qc.items`. The guide prints these in a "Quality checks" box. If `qc` is missing, the guide shows a red "draft" warning.

**Gate 1: Ballot match** (automated, blocking)

```bash
python scripts/verify_ballot.py --pdf ballot.pdf --json ballot.json \
    --html guide.html --html cheatsheet.html --report qc_report.md
```

- **Must exit 0 with 0 errors.** It checks four things:
  - every name in `ballot.json` is on the ballot (a missing name means a hallucination or misspelling);
  - contests and names are in ballot order;
  - both outputs number contests 1..N;
  - each number lists the right candidates.
- **Read every warning.** Warnings flag ballot lines that look like candidates you didn't capture, and write-in or measure counts that don't match. Resolve each one or explain it in the report.
- **Check the reading order.** If column detection looks wrong, check the "ballot text in reading order" dump in the report, then rerun with `--columns 1` or `3`.
- **Spot-check by eye.** Render the ballot pages to PNG and compare the first, a middle and the last contest on each page against the cheat sheet.
- **No PDF:** run without `--pdf`, and state prominently in the guide and to the user that names and order were not verified against the official ballot.

**Gate 2: Every fact has a source.** Every candidate fact, poll and dollar figure must trace to a link stored in `ballot.json`. Delete anything you can't source, or mark it "(unverified)". The checker warns on contested candidates with no links.

**Gate 3: Independent fact-check** (blocking)

- **Who checks.** Spawn a fresh subagent with no drafting context. Give it `ballot.json` and ask it to verify claims against the cited sources (and fresh searches), in priority order:
  1. Numbers: polls, vote counts, money, dates.
  2. Biographies: offices held, years, employers.
  3. Quotes and attributed stances, especially on local issues.
  4. Endorsements.
  5. Anything stale, such as withdrawals, court rulings or newer polls.
- **What it returns.** WRONG, UNSUPPORTED and STALE lists, each with URLs.
- **What you do with it.** Correct every WRONG item, and correct or remove every UNSUPPORTED item. Re-run Gate 1 after any edit.
- **No subagent tool.** Do a second pass yourself with fresh searches, and say in `qc.items` that it was a self-check, not independent.

**Gate 4: Voting rules.** Every voting-rules bullet has an official source fetched this session, and every date's weekday is correct.

**Gate 5: Visual check.** Render two or three guide pages and the cheat sheet to PNG and look at them once. Check for clipped text, overlaps, the cheat sheet fitting one page, and party colors.

**When a gate fails:** if you can't make a gate pass, don't present the output as final. Tell the user exactly what failed. Deliver only as "DRAFT – not verified" if they still want it.

## Step 7: Deliver

- Before publishing, load the `artifact-design` skill. Then publish `guide.html` as an artifact and send both PDFs plus `qc_report.md`.
- **Tell the user, in one line each:**
  - What the checks covered, e.g. "71/71 contests and every name matched the ballot; 3 claims corrected after fact-check."
  - The artifact is private until they share it from the page's Share menu.
  - The cheat sheet is for marking in pen and bringing to vote. State this state's rule on phones and notes.
- **Offer one next step at most:** a scheduled recheck of polls and late news a few days before Election Day, or before the last day of early voting if the state has one. A recheck reruns all five gates before republishing to the same artifact.
