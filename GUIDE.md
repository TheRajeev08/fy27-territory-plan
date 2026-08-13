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

---

## Every time you want a plan

**1. Export from SuperDash** and save the `.xlsx` or `.csv` (Downloads is fine).

**2. In Copilot, type:**

> Build my FY27 territory plan

**3. It will ask for your file** — drag the file into the chat window, or paste its location.

**4. Wait 1–2 minutes.** It cleans your list (duplicates, parent/child rollups), sorts every
account into a play, pulls your live Salesforce and Gong activity using *your* login, and ranks
who to contact first.

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
| No Revenue MCP access at all | Use the browser version: <https://therajeev08.github.io/fy27-territory-plan-team/> — no CRM, but classification, Sprint Focus and Excel export all work |

Your CRM data stays on your machine, runs under your own credentials, and is never shared
between teammates.
