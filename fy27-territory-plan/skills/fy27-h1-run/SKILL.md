---
name: fy27-h1-run
description: "Run the complete FY27 H1 territory build end to end from a SuperDash export: classify the book into Innovate/Trust/Scale, enrich from Salesforce and Gong, re-base sizing on live licensing, rank the H1 focus accounts, build the GHCP sprint priority queue, and render the leadership deck, evidence deck and Excel workbooks — then verify the result is shippable. Use for 'build my FY27 territory plan and deck', 'full territory run', 'run the whole thing from my SuperDash export', 'territory plan and leadership deck', 'H1 plan end to end', 'do the complete FY27 build', or when a teammate uploads a Super Summary export and wants everything."
---

# FY27 H1 — End-to-End Run

> **If this file was uploaded into the chat rather than loaded as an installed skill, stop.**
> It is the front door only: the phase skills and their scripts are not present, so nothing here
> can actually run. Do not improvise a simplified plan and do not ask for more files to be
> uploaded — skills load from `~/.copilot/installed-plugins/`, never from chat attachments.
> Tell the teammate to run this in Terminal, then fully quit Copilot (`Cmd + Q`) and reopen:
>
> ```bash
> curl -fsSL https://raw.githubusercontent.com/TheRajeev08/fy27-territory-plan/main/install.sh | bash
> ```

## Mission

One instruction in, four artefacts out. The teammate gives you a SuperDash export; you return the
territory plan, the GHCP sprint queue, the leadership deck and the evidence pack, and you tell them
plainly what is thin.

This skill is the **front door**. It owns the *order* and the *invariants*. It does not own any
arithmetic — every number is produced by the scripts in the three phase skills:

| Phase skill | Owns |
|---|---|
| **fy27-territory-plan** | classification, engagement scoring, the workbook, the sprint queue |
| **fy27-crm-enrichment** | the pinned Salesforce and Gong queries |
| **fy27-h1-focus-deck** | sizing, licensing, ranking, PAF, coverage, both decks |

Run those skills' pipelines as written. Do not paraphrase their steps or recompute their outputs.

## The ordering rule this skill exists to enforce

**The workbook must be rebuilt after the deck phase, not during the plan phase.**

`workbook.py` only emits the GHCP sprint layout when **both** `focus-accounts.json` (from ranking)
and `licensing.json` (from the deck phase) are already in the run directory. Rebuild it earlier and
the Sprint Focus sheet silently falls back to a narrower rank-ordered layout, with no error and a
zero exit code. The run looks finished. The GHCP segments are simply gone.

That is the single most common way this build goes wrong, and it is why step 8 exists.

## Step 0 — preflight

```bash
python3 -m pip install --user python-pptx xlsxwriter
python3 SCRIPTS/seller_profile.py show
```

`SCRIPTS` is this skill's `scripts/` directory.

`show` prints the teammate's saved profile and a `missing` list. On a first run it seeds the
profile from the shipped `targets.json`, so anyone who had been editing that file by hand keeps
their numbers.

**Ask only for what `missing` lists.** Do not re-interview a teammate who already has a profile —
confirm the territory and the headline targets and move on. Write answers back with:

```bash
python3 SCRIPTS/seller_profile.py set --json '{"territory": "...", "targets": {...}}'
```

Anything the teammate does not have, leave unset. A `null` target renders **TBD** on the deck; a
zero renders as *achieved*. Never convert one into the other to make a chart look complete.

Then confirm what is available, because it changes what you can promise:

| Missing | Consequence — say this up front |
|---|---|
| Revenue MCP / Salesforce | engagement stays **Unknown**, no open pipeline, no Microsoft tiering |
| Kusto | no consumption actuals; Bucket 2 rests on the profile's run-rate base alone |
| `gh auth` | no PAF key actions; execution slides fall back to the shipped `paf.json` |

## Step 1 — classify

Follow **fy27-territory-plan** steps 1–2. Report the normalisation honestly: source rows, exact
duplicates, parent/child groups collated, de-duplicated account count, and accounts per play
including the Unclassified discovery queue.

## Step 2 — enrich

Follow **fy27-crm-enrichment**, then `enrich_activity.py`. If a source errors, name the source that
failed and carry on. **Never present an unenriched account as cold** — it is Unknown.

## Step 3 — re-base sizing on live licensing

Follow **fy27-h1-focus-deck** step 0, then step 1 (`licensing.py`, then `potential.py`).

This is not optional polish. The SuperDash export reports signals org-wide and overstates the
billable population — badly for GHAS, which bills per **active committer**, not per seat. Store the
`get_licensing_summary` responses verbatim so the sizing can be audited later.

## Step 4 — actuals, Microsoft overlap, pipeline

Follow **fy27-h1-focus-deck** steps 2, 5 and 6. Tier the Microsoft overlap properly:

- TPID **and** a named owner → co-sell led
- TPID alone → partner led
- neither → direct

A TPID on its own is close to the default state of a book. Reporting it as co-sell overstates
Microsoft leverage on a slide leadership will push on.

## Step 5 — triggers and ranking

Follow **fy27-h1-focus-deck** steps 3, 4 and 7. **Every trigger carries a date and a source, or it
is dropped.** Step 8's verifier fails the run on an undated trigger.

## Step 6 — seller corrections

Follow **fy27-h1-focus-deck** step 8. Corrections go into `overrides.json` as **facts**, never as
forced rankings: fix the underlying input and let the weights move the account — then tell the
teammate where it actually landed, including when it did not move.

Report anything in `overridesUnmatched`. A typo'd account name fails silently otherwise.

## Step 7 — conversations, learnings, decks

For the account worked in PAF detail on each play slide, gather the **real conversation** into
`conversations.json` first — what they agreed to, what is blocking, what they committed to. Walk
the account hierarchy and search Gong **by name as well as by ID**: calls get filed under whichever
record the meeting was booked under. Where there is genuinely no call, write "no call record"
rather than implying contact.

Then **fy27-h1-focus-deck** steps 9 and 10: `learnings.py`, `exec_deck.py`, `deck.py`,
`focus_workbook.py`.

Pass the run-local targets file rendered from the profile — never the shipped one:

```bash
python3 SCRIPTS/seller_profile.py render "<RUN>"
python3 DECK_SCRIPTS/targets.py "<RUN>/potential.json" "<RUN>/focus-accounts.json" "<RUN>" \
        --targets "<RUN>/targets.json"
```

`targets.py` takes **three positional arguments** before its flags. Called with fewer it prints its
docstring, writes nothing, and the deck renders `$0 / TBD` with no error.

## Step 8 — rebuild the workbook, then verify

Only now, with licensing and the ranked focus set both in place:

```bash
python3 PLAN_SCRIPTS/workbook.py --from-report "<RUN>"
python3 SCRIPTS/verify_run.py "<RUN>"
```

Always `--from-report`. The normal invocation re-derives the report from the raw export and
discards every override applied since.

`verify_run.py` exits non-zero when the run is not shippable. It checks that all four artefacts
exist and are non-trivial, that Sprint Focus is in the **GHCP layout** rather than the fallback,
that the priority accounts are listed above the queue, that coverage has a denominator, that every
override matched, and that every trigger is dated. **Fix what it reports; do not explain it away.**

Then run the deck checks and read the result back:

```bash
python3 DECK_SCRIPTS/verify_deck.py "<RUN>/fy27-h1-leadership.pptx" --coverage "<RUN>/coverage.json"
python3 DECK_SCRIPTS/verify_deck.py "<RUN>/fy27-h1-focus-accounts.pptx"
```

`verify_deck.py` passing is **not sufficient** — its geometry checks pass stale numbers happily.
Read back the rendered text of slides 1, 6, 9 and 10 before handing over.

## Rules held throughout

- **Deterministic Python owns all arithmetic and rendering. You only gather evidence.** Never
  compose a dollar figure, an account count or a ranking in chat.
- **Overrides supply missing facts, never forced rankings.**
- **Potential is not pipeline.** No slide carries modelled potential ARR. Size in units the
  teammate can verify — seats, active committers, invoiced credits.
- **Bucket 2 is a run rate, not a booking gap.** Do not add seat landings on top of the carry, and
  do not count open metered pipeline already inside it.
- **Copilot seat headroom counts installed GHE only.** A seat that has not landed cannot have
  Copilot attached to it.
- **State coverage, never imply completeness.** Where activity, partner mapping or Microsoft owner
  data is thin, say so on the slide. That is what makes the asks credible.
- **Everything stays in the run directory.** `overrides.json`, `asks.json` and `conversations.json`
  name customers. They never leave it, and they are never committed.

## Hand-off

Tell the teammate:

- both deck paths and both workbook paths
- the account / tier / play mix
- **coverage per bucket** — this is what leadership pushes on
- how many focus accounts carry a dated trigger and how many do not
- anything in `overridesUnmatched`
- every `WARN` from `verify_run.py`, in their words rather than the tool's

## Re-running later

Never start a fresh run to refresh an existing one — overrides, asks and conversations live in the
run directory and a new run does not have them.

> Refresh from the existing run with the latest Salesforce activity, keep my overrides, and rebuild
> the workbook and both decks.

That path re-runs enrichment, licensing and ranking against the same run directory, then repeats
step 8. Quota changes go through `seller_profile.py set` and a `render`, never by editing the
shipped `targets.json`.
