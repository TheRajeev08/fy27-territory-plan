---
name: fy27-territory-plan
description: "Build an FY27 GitHub territory plan from a SuperDash export, enriched live from Salesforce and Gong. Classifies every account into the Innovate, Trust, and Scale revenue plays, reports duplicate/parent-child normalization, scores engagement and a meeting-booking Sprint Focus shortlist, renders an interactive app, and exports an Excel workbook. Use for 'build my territory plan', 'FY27 book of business', 'SuperDash plan', 'which accounts go in which play', or 'territory plan for my sales leader'."
---

# FY27 Territory Plan

## Mission

Turn a seller's SuperDash export into a territory plan they can hand to a sales leader:
every account bucketed into **Innovate**, **Trust**, **Scale**, or **Unclassified**, with live
Salesforce and Gong engagement, a meeting-booking shortlist, and an Excel workbook.

The enrichment runs on **the invoking teammate's own MCP credentials**. Nothing is shared, nothing
is cached across users, and no credential ever reaches a browser.

## When to invoke

- "Build my FY27 territory plan from <file>"
- "Which of my accounts are Innovate / Trust / Scale?"
- "Prep my book of business for the QBR"
- "Refresh my territory plan with the latest Salesforce activity"

## Inputs

A SuperDash export (`.xlsx` or `.csv`). Accept an absolute path or an attachment. If the teammate
has not given one, ask for the file path — do not guess.

## Pipeline

Run these in order. `SCRIPTS` is this skill's `scripts/` directory.

### 1. Create an isolated run

```bash
python3 SCRIPTS/new_run.py "<path to SuperDash export>"
```

Returns `runDir`, `inputPath`, `sourceName`. Use `runDir` for everything that follows. Never write
results into the plugin directory or into another run.

### 2. Classify the book

```bash
python3 SCRIPTS/workbook.py "<inputPath>" "<runDir>" "" "<sourceName>"
```

Returns `reportPath`, `workbookPath`, `accountCount`. Read `reportPath` and report to the teammate:

- source rows, excluded rows, exact-duplicate groups, parent/child groups collated
- de-duplicated account count
- accounts per play, including the Unclassified discovery queue

Do **not** restate or reinvent the classification rules. `workbook.py` owns them; describing them
differently in chat is how the plan and the workbook drift apart.

### 3. Enrich from Salesforce and Gong

Follow the **fy27-crm-enrichment** skill. It holds the pinned queries, the batching rules, and the
guardrails. It produces one raw JSON file; then:

```bash
python3 SCRIPTS/enrich_activity.py "<runDir>/raw-crm.json" "<runDir>"
```

If the teammate has no Revenue MCP access, or Salesforce/Gong errors, skip this step and say
plainly which source was unavailable. The plan is still valid — engagement simply stays **Unknown**.
Never present an unenriched account as cold.

### 4. Rebuild with engagement, then score the sprint

```bash
python3 SCRIPTS/workbook.py "<inputPath>" "<runDir>" "<runDir>/salesforce-activity.json" "<sourceName>"
python3 SCRIPTS/sprint_score.py "<runDir>/fy27-territory-plan.json"
python3 SCRIPTS/workbook.py "<inputPath>" "<runDir>" "<runDir>/salesforce-activity.json" "<sourceName>"
```

The final `workbook.py` call is required: it is what folds the Sprint Focus sheet into the workbook.

### 5. Render in the app

```
open_canvas(canvasId: "fy27-territory-plan", instanceId: "fy27-territory-plan",
            input: { reportPath: "<runDir>/fy27-territory-plan.json",
                     inputPath:  "<runDir>/<uploaded file>" })
```

The canvas derives everything from `reportPath`, so it always shows that run's data.

### 6. Hand off

Give the teammate:

- the play distribution and what changed after enrichment
- coverage: how many accounts matched activity, how many are Unknown, as-of date, window
- the top Sprint Focus accounts and why each is ranked there
- the workbook path (`<runDir>/FY27 Territory Plan.xlsx`)

## How to talk about the plays

When the teammate asks how to actually win an account, use the **paf** skill for GitHub's Product
Adoption Framework key actions, and keep the motion tied to the account's observed product signals.

| Play | What qualifies an account | Where to take it |
|---|---|---|
| **Innovate** | Copilot whitespace, AI/developer-productivity headroom | Developer experience and velocity; land Copilot where the seats already exist |
| **Trust** | Security whitespace, GHAS gap against GHE footprint | Secure the SDLC; AppSec and platform-security owners |
| **Scale** | Actions/ADO migration TAM, metered consumption growth | Platform consolidation and CI/CD standardization |
| **Unclassified** | No qualifying product signal in this upload | Discovery queue — never assign a play without evidence |

## Guardrails

- **Decision support, not forecast.** Scores are hypotheses requiring seller validation. Never
  present potential, engagement, or readiness as ARR, pipeline, or propensity.
- **Unknown is not cold.** An account with no matched activity is Unknown. Say so.
- **Scope.** Only accounts present in the uploaded file are ever queried or reported.
- **Isolation.** All output lives in the teammate's run directory under
  `~/.copilot/fy27-territory-plan/runs/`. Never commit it, never copy it between teammates.
- **One source of truth.** `workbook.py` owns classification and scoring; `enrich_activity.py`
  owns engagement arithmetic. Do not compute either in chat.

## Fallback

Teammates without Revenue MCP access can use the browser app at
<https://therajeev08.github.io/fy27-territory-plan-team/>, which does classification, Sprint Focus,
and Excel export locally with no CRM. It also supports the older manifest export / enrichment import
handoff if someone else runs the enrichment for them.
