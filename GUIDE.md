# FY27 Territory Plan — Teammate Guide

## What this does

You give it your SuperDash export. It returns your accounts sorted into the
**Innovate / Trust / Scale** plays, tells you **who to book meetings with first**, and
produces an Excel workbook you can hand to your leader.

---

## One-time setup (about 2 minutes)

**1. Open Terminal** — press `Cmd + Space`, type `Terminal`, press Enter.

**2. Paste this one line and press Enter:**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRajeev08/fy27-territory-plan/main/install.sh | bash
```

Wait for it to say **"Done."** If it asks for your Mac password, type it — the screen won't
show characters as you type, which is normal.

**3. Quit Copilot completely** (`Cmd + Q`) and reopen it. Closing the window is not enough.

You never need to do this again.

**If the plan doesn't run**, check the install before anything else. Paste this into
Terminal — it prints exactly what is missing, and it is much faster than describing the
symptom:

```bash
bash ~/.copilot/installed-plugins/fy27-territory-plan/doctor.sh
```

Do **not** upload any of the plugin's files into the Copilot chat window. They are
documentation, not an installer — Copilot will try to work from them and quietly build a
stripped-down plan with none of the live data.

---

## Every time you want a plan

**1. Export from SuperDash** and save the `.xlsx` or `.csv` (Downloads is fine).

**2. In Copilot, type:**

> Build my FY27 territory plan and leadership deck

(Just the plan, no deck? Ask for **"build my FY27 territory plan"** instead.)

**3. It will ask for your file** — drag the file into the chat window, or paste its location.

**4. The first time only, it asks for your territory and quota.** It remembers them, so later runs
skip straight past. Anything you don't have, say so — it prints **TBD** rather than guessing.

**5. Wait a few minutes.** It cleans your list (duplicates, parent/child rollups), sorts every
account into a play, pulls your live Salesforce and Gong activity using *your* login, ranks who to
contact first, and builds your deck. It checks its own work at the end and tells you if anything
came out thin.

---

## What you get back

**In chat:** account totals, duplicates merged, the split across plays, and your top Sprint Focus
accounts with the reason each one ranks there.

**An Excel workbook** with 8 tabs:

| Tab | What's in it |
|---|---|
| Executive Summary | The one page for your leader |
| All Accounts | Everything, with play + engagement |
| Innovate / Trust / Scale | One tab per play |
| Unclassified | Discovery queue — no product signal yet |
| **Sprint Focus** | Who to book **this** sprint, ranked |
| Methodology | How it decided, for when you're challenged |

---

## Building the leadership presentation

Once the plan has run, ask for the H1 deck:

> Build my H1 focus accounts deck

This takes longer — 10–20 minutes — because it researches live news for each candidate account
before it ranks them. Leave it running.

**What you get:** a PowerPoint naming **30–50 focus accounts for the half**, answering the seven
questions a leader will ask:

| Slide | Question it answers |
|---|---|
| Key accounts | Which accounts, tiered Must-win / Build / Develop, and why now |
| Plays | Which play runs on each, and the first move for each play |
| Potential | The prize in dollars: AIU, Copilot seats, GHE + GHAS seats, ACR and ARR |
| **How I win** | One slide per play, grounded in GitHub's Product Adoption Framework, plus the operating cadence and half-level milestones |
| Leverage | Your mapped partners, their GitHub PDM, and Microsoft CSP involvement |
| Honest read | What's working and what isn't, with the numbers attached |
| Asks | What you need from leadership, Partnerships, Marketing and Ops |

Alongside it you get an **evidence workbook**. When someone challenges a number on a slide, the
`Sizing Detail` tab shows exactly where it came from — the quantity, the rate, and whether that
rate was observed on the account, taken from published pricing, or derived.

**Ask for a different number of accounts** any time:

> Build my H1 deck with 30 accounts

---

## Reading the plays

| Play | Why an account landed here | Your angle |
|---|---|---|
| **Innovate** | Copilot whitespace, AI/productivity headroom | Developer velocity — land Copilot where seats already exist |
| **Trust** | Security gap against their GitHub footprint | Secure the SDLC — AppSec and platform-security owners |
| **Scale** | Actions / ADO migration TAM, metered growth | Platform consolidation, CI/CD standardization |
| **Unclassified** | No qualifying signal in this upload | Discovery — never assign a play without evidence |

**Sprint Focus tiers:** *Priority* = two-way conversation **and** meetings happening.
*High* = one or the other. *Medium/Low* = no recent contact, ranked by account potential.
*Unranked* = no activity data matched.

**Ask follow-ups in the same chat**, e.g. *"How do I win the Trust accounts?"* — it pulls GitHub's
Product Adoption Framework for concrete next actions tied to each account's product signals.

---

## Two things to be careful about

- **"Unknown" does not mean cold.** It means no logged activity matched — often just CRM hygiene.
  Don't deprioritize an account on that alone.
- **Scores are hypotheses, not forecasts.** They tell you where to *look*, not what will close.
  Validate the stakeholder and a dated next step in Salesforce before it goes into a plan.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| "Done." never appeared | Re-run the same command — it is safe to repeat and repairs itself |
| Copilot doesn't recognize the request | The app wasn't fully quit. `Cmd + Q`, reopen, try again |
| Plan works but no Salesforce/Gong data | You need the `github-revenue` plugin connected and Salesforce-authenticated. Everything else still works |
| Excel file won't generate | Run `python3 -m pip install --user xlsxwriter` |
| Presentation won't generate | Run `python3 -m pip install --user python-pptx` |
| Deck says "no partner relationships mapped" | That's a data gap, not an error — partner records exist per opportunity, and most accounts have none. The deck turns it into an ask |
| Deck shows 0 triggers for most accounts | Only news with a real date *and* a real source link is counted. Unverifiable claims are dropped on purpose |
| No Revenue MCP access at all | Use the browser version: <https://therajeev08.github.io/fy27-territory-plan-team/> — no CRM, but classification, Sprint Focus and Excel export all work |

Your CRM data stays on your machine, runs under your own credentials, and is never shared
between teammates.
