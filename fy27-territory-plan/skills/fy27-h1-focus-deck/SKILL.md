---
name: fy27-h1-focus-deck
description: "Build the FY27 H1 focus-accounts leadership presentation from a completed territory plan run. Selects 30-50 focus accounts ranked on potential ARR, active communication and dated live triggers; sizes the opportunity in AIU, Copilot seats, and GHE+GHAS seats/ACR/ARR; grounds the execution plan in GitHub's Product Adoption Framework; and renders a PowerPoint plus an evidence workbook. Use for 'H1 focus accounts', 'build my territory presentation', 'which 40 accounts for the half', 'focus account deck', 'presentation for my sales leader', or 'H1 plan for FY27'."
---

# FY27 H1 Focus Accounts — Leadership Presentation

## Mission

Turn a completed territory-plan run into the presentation a sales leader actually asks for:
**30–50 focus accounts for H1**, sized in dollars, with a named execution plan, Microsoft and
partner leverage, an honest read on what is and is not working, and specific asks.

The deck answers seven questions, in this order:

1. What are the key accounts?
2. What plays run across them?
3. What is the potential — AIU, Copilot seats, GHE + GHAS (seats, ACR, ARR)?
4. **How will I achieve it?** — weighted heaviest, one slide per play plus the operating cadence
5. Where is the Microsoft overlap, and how do I leverage Microsoft and partners?
6. What is working and what is not?
7. What is the ask of leadership and supporting functions?

## Prerequisite

A completed **fy27-territory-plan** run. This skill consumes that run directory; it does not
re-classify the book. If the teammate has not run the territory plan yet, run it first — the
play assignment lives there and must not be recomputed here.

`python-pptx` and `xlsxwriter` are required:

```bash
python3 -m pip install --user python-pptx xlsxwriter
```

## The rule that keeps this honest

**Deterministic Python owns all arithmetic and rendering. The agent only gathers evidence.**

Never compose slide content, dollar figures, account counts, or rankings in chat. Every number on
a slide is computed by these scripts from the run's own JSON. This is what stops the deck from
drifting away from the workbook it is supposed to summarise.

## Pipeline

`SCRIPTS` is this skill's `scripts/` directory. `RUN` is the territory-plan run directory.

### 1. Size the potential

```bash
python3 SCRIPTS/potential.py "<RUN>/fy27-territory-plan.json" "<RUN>"
```

Sizes each account from its observed product signals using the rates in `pricing.json`. Every
sized line carries a **basis**: `observed` (this account's own price), `list` (published GitHub
pricing), or `derived` (a median where no list price exists — GHE only). Accounts with no product
signal are not sized; they are reported as needing discovery. Nothing is ever sized without a
signal.

Writes `<RUN>/potential.json`.

### 2. Add Kusto actuals

```bash
python3 SCRIPTS/actuals.py --print-queries
```

Run the printed KQL through `revenue-mcp-server/query_kusto` (database `rev_source`), save each
result, then:

```bash
python3 SCRIPTS/actuals.py "<RUN>" --arr <file> --consumption <file>
```

This attaches current ARR, seats by product, and annualised consumption including `copilot aiu`.
If the teammate has no Kusto access, skip it — the deck will lead on potential and say plainly
that installed-base figures were unavailable.

### 3. Stage 1 — pick the trigger candidates

```bash
python3 SCRIPTS/rank.py stage1 "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" "<RUN>" --count 60
```

Ranks on potential and communication only, and writes `<RUN>/trigger-candidates.json`. Triggers are
researched **after** this, not before — otherwise the ranking would depend on triggers that were
only fetched for accounts the ranking already favoured.

### 4. Research live triggers

For the candidates, use `web_search` (batch them across parallel research sub-agents; ~10 accounts
per agent keeps each one reliable). Ask for a single raw JSON object:

```json
{"accounts": {"<salesforceId>": [
  {"type": "funding", "date": "YYYY-MM-DD", "headline": "...",
   "url": "https://...", "soWhat": "one line on why GitHub matters now"}]}}
```

`type` must be one of: `funding`, `acquisition`, `merger`, `ai_launch`, `security_incident`,
`leadership_change`, `expansion`, `layoff`, `earnings`, `partnership`, `product_launch`,
`regulatory`.

**Drop any trigger without both a real date and a real source URL.** An undated claim is a rumour,
and a leader will find it. Only the last 18 months count. Merge the agent payloads into
`<RUN>/triggers.json`, stripping any markdown fences the agents add.

### 5. Enrich partners and Microsoft overlap

Partner relationships hang off **opportunities**, not accounts, so query them that way:

```sql
SELECT Opportunity__r.AccountId, Partner_Name_Text__c, Partner_Involvement_PL__c,
       Source__c, CSP_Partner__c, Channel_Account_Manger_Name__c
FROM Partner__c WHERE Opportunity__r.AccountId IN (<focus account ids>)
```

`Channel_Account_Manger_Name__c` is the GitHub Partner Development Manager — surface it, it is the
name the teammate needs. Shape the result as
`{"accounts": {<accountKey>: {"partners": [...], "pdm": [...], "microsoft": {"csp": bool}}}}`
and save as `<RUN>/partners.json`.

Report coverage honestly. `get_account_partners` on an account ID returns nothing for most
accounts; that is a data gap, not evidence that no partner exists.

### 6. Stage 2 — final ranking

```bash
python3 SCRIPTS/rank.py stage2 "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" "<RUN>" \
  --triggers "<RUN>/triggers.json" --count 40
```

Re-ranks on the full composite — potential ARR, active communication, and trigger recency and type
— and cuts tiers at the top 25% (Tier 1 – Must win), next 35% (Tier 2 – Build), remainder
(Tier 3 – Develop). Use `--count` between 30 and 50.

### 7. Build the deck and the evidence workbook

```bash
python3 SCRIPTS/deck.py "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" \
  "<RUN>/focus-accounts.json" "<RUN>" --partners "<RUN>/partners.json"

python3 SCRIPTS/focus_workbook.py "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" \
  "<RUN>/focus-accounts.json" "<RUN>" --partners "<RUN>/partners.json"
```

The deck is the argument; the workbook is the evidence. `Sizing Detail` gives one row per product
line with its rate and basis, so any figure on a slide can be traced in a single lookup.

### 8. Hand off

Give the teammate:

- the deck path and the account/tier/play mix
- total potential ARR against current ARR, and the sizing coverage behind it
- how many accounts carry a dated trigger, and how many do not
- the workbook path, and the fact that `Sizing Detail` is where challenges get settled

Offer to preview the deck by opening the `powerpoint` canvas on the generated file.

## Execution guidance comes from PAF

The Q4 slides are grounded in real **Product Adoption Framework** key actions, baked into
`paf.json` at build time by `build_paf.py`. Each play gets a **land** sequence for greenfield
accounts and an **expand** sequence for accounts with a footprint, and the appendix carries the
real resource links.

Regenerate only when PAF itself changes:

```bash
python3 SCRIPTS/build_paf.py   # requires gh auth; writes paf.json
```

Do not invent adoption steps in chat. If a key action is not in `paf.json`, it is not in the deck.

## Guardrails

- **Potential is not pipeline.** It is an opportunity size derived from product signals, to be
  qualified in discovery. Never present it as forecast, commit, or propensity.
- **AIU stays out of potential ARR.** Consumption already invoiced is existing revenue, and
  included credits ship bundled with the seat. Counting either as upside double-counts the book.
  The deck shows AIU as measured run-rate and as capacity unlocked, separately.
- **Every trigger is dated and cited, or it is dropped.**
- **State coverage, never imply completeness.** Where activity, partner mapping, or Microsoft AM
  data is thin, the deck says so on the slide. That is deliberate — it is what makes the asks
  credible.
- **GHE has no public per-seat price.** Its rate is a derived median and is labelled `derived`
  everywhere it appears. Say so if asked.
- **Isolation.** Everything is written into the teammate's own run directory. Never commit it,
  never copy it between teammates.
