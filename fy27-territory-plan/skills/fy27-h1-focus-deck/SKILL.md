---
name: fy27-h1-focus-deck
description: "Build the FY27 H1 focus-accounts leadership presentation from a completed territory plan run. Selects 30-50 focus accounts ranked on potential ARR, live open pipeline, active communication and dated live triggers; sizes the opportunity in AIU, Copilot seats, and GHE+GHAS seats/ACR/ARR; scores quota coverage per bucket against the teammate's targets; grounds the execution plan in GitHub's Product Adoption Framework; and renders a 10-slide leadership deck, a 21-slide evidence deck and an evidence workbook. Use for 'H1 focus accounts', 'build my territory presentation', 'which 40 accounts for the half', 'focus account deck', 'leadership deck', 'presentation for my sales leader', 'how do I make my number', or 'H1 plan for FY27'."
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

`type` must be one of the types `rank.py` can score: `funding`, `acquisition`, `security_incident`,
`leadership_change`, `ai_launch`, `product_launch`, `expansion`, `partnership`, `earnings`,
`recognition`, `other`. Anything else is dropped, so do not invent types.

**Drop any trigger without both a real date and a real source URL.** An undated claim is a rumour,
and a leader will find it. Only the last 18 months count.

Write each agent's raw reply to its own file in `<RUN>/triggers/`, then merge:

```bash
python3 scripts/merge_triggers.py <RUN>/focus-candidates.json <RUN>/triggers <RUN>/triggers.json
```

`merge_triggers.py` strips markdown fences, resolves whichever identifier the agent used
(Salesforce id, account name, or candidate key) back onto the candidate key, enforces the
type/date/URL bar, and reports `dropped` plus `unmatchedKeys`. A non-zero `unmatchedKeys`
usually means the agent researched an account that is not in the candidate set — check it
rather than ignoring it.

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

### 6. Targets, Microsoft overlap and open pipeline

Set the teammate's quota in `SCRIPTS/targets.json` — Bucket 1 is GHE + GHAS, Bucket 2 is
consumption (Copilot, AI credits, Actions, Codespaces, Code Quality). Leave a target `null`
if it is not yet set; the deck renders `TBD` and suppresses the attainment percentage rather
than inventing a denominator. Targets are **net-new**; renewals are reported separately.

Pull Microsoft TPIDs and open opportunities:

```bash
python3 SCRIPTS/crm_context.py query "<RUN>/focus-accounts.json"
```

Run each emitted SOQL query with `query_salesforce`, save the combined result as
`{"accounts": [...], "opportunities": [...]}`, then:

```bash
python3 SCRIPTS/crm_context.py ingest "<RUN>/crm/raw.json" "<RUN>"
python3 SCRIPTS/plays.py "<RUN>"
python3 SCRIPTS/targets.py "<RUN>/potential.json" "<RUN>/focus-accounts.json" "<RUN>"
```

**`plays.py` must run after CRM ingest and before stage 2.** Play is assigned in
`workbook.py` from the account's own product footprint, using a deterministic ladder:

| Condition | Play |
|---|---|
| Not on GHE | **Scale** — this is the migration and displacement play |
| On GHE, Copilot on ≥ 50% of GHE licences | **Trust** |
| On GHE, Copilot on < 50% | **Innovate** |
| On GHE with GHAS, no Copilot | **Trust** — security has already landed |
| On GHE, neither, **regulated** industry | **Trust** |
| On GHE, neither, not regulated | **Innovate** |

The last two rungs need `Account.Industry`, which only arrives with CRM ingest. Accounts
waiting on it are marked `playPendingIndustry` and default to Innovate; `plays.py` resolves
them once industry is known. It can only move an account **between Trust and Innovate**, never
in or out of the play set, so the stage-1 candidate list cannot change depending on whether
enrichment ran. Where industry is blank or miscoded, correct it in `overrides.json` with
`industry` / `regulated` / `industryReason`, or assert the play directly with `play` /
`playReason`.

TPIDs live on `MSFT_TPID__c`, `MSFT_All_TPIDs__c` and `MS_Sales_TPID_Best_Match__c`. There is
no `TPID__c`. An account with a TPID is run as co-sell with the Microsoft account team and a
delivery partner.

Opportunities whose close date has already passed are flagged **stale** and scored as zero.
They are reported as a hygiene finding, never counted as coverage — a past-dated deal is not
forecastable whatever its stage says.

### 7. Stage 2 — final ranking

```bash
python3 SCRIPTS/rank.py stage2 "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" "<RUN>" \
  --triggers "<RUN>/triggers.json" --crm "<RUN>/crm-context.json" --count 40 \
  --overrides "<RUN>/overrides.json"
```

Re-ranks on the full composite — **potential ARR 40, live H1 pipeline 20, active communication
20, trigger recency and type 20** — and cuts tiers at the top 25% (Tier 1 – Must win), next 35%
(Tier 2 – Build), remainder (Tier 3 – Develop). Use `--count` between 30 and 50. Pipeline value
is discounted by how far the best live opportunity has advanced, so a large deal parked early
cannot outrank a smaller one near close.

### 8. Seller corrections — `overrides.json`

Salesforce is never fully current. The seller knows things the CRM has not been told: a deal
agreed but not yet raised, a conversation that happened off-system, a partner flag that is
wrong. `overrides.json` in the run directory carries those facts into the arithmetic so they
survive a re-run.

**The rule that makes this safe: overrides supply missing facts, never forced rankings.**
The deck states its accounts are ranked on potential, pipeline, communication and triggers.
Pinning an account to a rank would make that sentence false. Correct the underlying fact and
let the existing weights move the account — or report that they did not.

```jsonc
{
  "accounts": {
    "001XXXXXXXXXXXXXXX": {              // Salesforce ID, with name fallback
      "name": "Indus Valley Partners",
      "pipeline": [                       // sized through pricing.json, never typed as dollars
        {"product": "GHE",  "seats": 335,      "quarter": "FY27 Q1", "reason": "agreed, not yet raised"},
        {"product": "GHAS", "committers": 285, "quarter": "FY27 Q1", "reason": "agreed, not yet raised"}
      ],
      "engagement": {"twoWay": true, "meetings": 1, "reason": "live GHAS discussion"},
      "msftOverlap": false                // e.g. GitHub-direct account wrongly carrying TPIDs
    }
  }
}
```

Then apply and re-run the downstream steps:

```bash
python3 SCRIPTS/overrides.py check "<RUN>/overrides.json" "<RUN>/focus-accounts.json"
```

Four guarantees, each deliberate:

* **Unmatched keys are fatal.** A typo'd Salesforce ID silently doing nothing is worse than a
  crash, because the correction looks applied and is not.
* **Manual pipeline is sized, not typed.** Seats and committers go through `pricing.json` at
  the same rates as every other line, so a seller-sourced number cannot drift off list.
* **Engagement overrides ride the real curve.** `apply_engagement()` imports `score_for()` from
  the `fy27-territory-plan` skill rather than reimplementing it, so an overridden account sits
  on the identical scoring curve as an un-overridden one.
* **Seller-sourced pipeline is visually distinct on the deck.** Leadership will look for these
  numbers in Salesforce. If they cannot find them and the deck did not say so, the deck loses
  credibility. Slide 6 footnotes the amount and the account.

Record any genuine assumption under an `assumption` key alongside `reason`, so the deck can be
defended line by line and the assumption can be reverted to see what moves.

#### Seller learnings

The computed learnings can be corrected or extended from the same file. Each entry may carry
`replaces` (a headline prefix; **fatal if it matches nothing**, so a reworded computed learning
can never leave the seller's version arguing beside it), plus `headline`, `detail`,
`carryForward` and `evidence`. Text may use the tokens `{focusTotal}`, `{ghasAccounts}`,
`{ghasPipeline}` and `{ghasCoverage}`, substituted from run data; an unresolved token is fatal.

```jsonc
"learnings": [
  {
    "replaces": "GHAS is a story we told",
    "headline": "GHAS is a strong product we under-narrated",
    "detail": "... {ghasPipeline} of GHAS is close-dated in H1, {ghasCoverage}x the target.",
    "carryForward": "Lead security conversations with the differentiators, not an attach ask."
  }
]
```

### 9. Derive the learnings

```bash
python3 SCRIPTS/learnings.py "<RUN>"
```

Computes the H2 carry-forward learnings and the working / not-working read from counts in the
run's own records. Nothing here is authored in chat.

### 10. Build the decks and the evidence workbook

```bash
# 10-slide executive cut - what gets presented in a 30-minute slot
python3 SCRIPTS/exec_deck.py "<RUN>" "<RUN>/fy27-h1-leadership.pptx"

# 21-slide evidence pack - the detail brought as backup
python3 SCRIPTS/deck.py "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" \
  "<RUN>/focus-accounts.json" "<RUN>" --partners "<RUN>/partners.json"

python3 SCRIPTS/focus_workbook.py "<RUN>/fy27-territory-plan.json" "<RUN>/potential.json" \
  "<RUN>/focus-accounts.json" "<RUN>" --partners "<RUN>/partners.json"
```

`exec_deck.py` imports its `Deck` class and theme from `deck.py`, so both decks stay visually
identical and only one file owns rendering behaviour. Its ten slides map to the seven questions:

| # | Slide | Question |
|---|---|---|
| 1 | Q1 scorecard — attainment against Bucket 1 and Bucket 2 | opener |
| 2 | H2 learnings carried forward | opener |
| 3 | Portfolio by play, with TPID flags | opener |
| 4 | Key accounts — Tier 1 must-wins | Q1 |
| 5 | The number — AIU, Copilot seats, GHE + GHAS | Q3 |
| 6 | Coverage — target vs live, dated pipeline | Q4 |
| 7 | How I get there — motions and account sequencing | **Q4** |
| 8 | Microsoft overlap and partner leverage | Q5 |
| 9 | What's working, what's not | Q6 |
| 10 | Asks — leadership and cross-functional | Q7 |

Question 2 is carried by slides 3 and 7 rather than a slide of its own, because plays only
matter in terms of which accounts and which motions.

**No slide carries modelled potential ARR.** Sizing is presented on slide 5 in units that can
be verified — seats, active committers, invoiced credits — and every dollar figure elsewhere is
dated pipeline, a set target, or invoiced attainment. Potential ARR still drives *ranking*
(`W_STAGE1` 0.65, `W_STAGE2` 0.40), because it is a reasonable relative ordering signal; it is
simply never shown as though it were money in hand.

Verify before handing off — the PowerPoint canvas is unreliable, so check the file itself:

```bash
python3 SCRIPTS/verify_deck.py "<RUN>/fy27-h1-leadership.pptx" --coverage "<RUN>/coverage.json"
python3 SCRIPTS/verify_deck.py "<RUN>/fy27-h1-focus-accounts.pptx"
```

Three defect classes, and a non-zero exit so it can gate a hand-off:

* **overflow** — estimated rendered text height against the box, plus any shape off the slide.
* **collision** — text shapes overlapping by more than 30% of the smaller one.
* **inconsistency** — headline figures on the slides against `coverage.json`, including a
  regression guard that the blended net-new figure never appears (it reads as Bucket 1
  coverage while containing Bucket 2 money).

Geometry alone has missed real text defects twice. **Also read the rendered text** of slides
1, 6, 9 and 10 after any narrative change — a stale count passes every geometry check.

The deck is the argument; the workbook is the evidence. `Sizing Detail` gives one row per product
line with its rate and basis, so any figure on a slide can be traced in a single lookup.

### 11. Hand off

Give the teammate:

- both deck paths — the 10-slide leadership cut and the 21-slide evidence pack
- the account/tier/play mix, and total potential ARR against current ARR
- **the coverage read per bucket**, because that is what leadership will push on
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
- **A focus account must belong to a play.** `rank.py` excludes unclassified accounts from both
  stages: the deck organises Q2 and Q4 by play, so an account with no play has nothing to be
  presented against no matter how large its potential is. It stays in the territory plan; it just
  cannot be a focus account until a product or usage signal classifies it.
- **State coverage, never imply completeness.** Where activity, partner mapping, or Microsoft AM
  data is thin, the deck says so on the slide. That is deliberate — it is what makes the asks
  credible.
- **GHE has no public per-seat price.** Its rate is a derived median and is labelled `derived`
  everywhere it appears. Say so if asked.
- **Isolation.** Everything is written into the teammate's own run directory. Never commit it,
  never copy it between teammates.
