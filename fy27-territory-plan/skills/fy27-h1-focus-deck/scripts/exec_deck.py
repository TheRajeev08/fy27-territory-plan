#!/usr/bin/env python3
"""FY27 H1 leadership deck - the 30-minute executive cut.

Ten slides answering the seven questions leadership asked, and nothing else. The long
deck (deck.py) remains the evidence pack; this is what gets presented. Theme and layout
primitives are imported from deck.py so both decks stay visually identical and only one
of them owns rendering behaviour.

    exec_deck.py <runDir> <out.pptx>

Reads focus-accounts.json, potential.json, coverage.json, crm-context.json,
learnings.json, partners.json and fy27-territory-plan.json from the run directory.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deck import (  # noqa: E402
    Deck, money, num, truncate,
    INK, PANEL, PANEL_2, LINE, TEXT, MUTED, WHITE, ACCENT, WARN, GOOD, PLAY_COLOR,
    MARGIN, BODY_TOP, W, H,
)
from pptx.util import Inches, Emu, Pt  # noqa: E402
from pptx.enum.text import PP_ALIGN  # noqa: E402

PLAYS = ("Innovate", "Trust", "Scale")

PLAY_THESIS = {
    "Innovate": "AI-native delivery - Copilot seats and AI credits as the entry motion",
    "Trust": "Secure the software supply chain - GHAS on committer bases already in place",
    "Scale": "Consolidate onto one platform - GHE migration and toolchain displacement",
}


def load(run_dir, name, default=None):
    try:
        with open(os.path.join(run_dir, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def ratio_color(value):
    if value is None:
        return MUTED
    if value < 1.0:
        return WARN
    if value > 5.0:
        return ACCENT
    return GOOD


def bucket_of(coverage, name):
    for bucket in coverage.get("buckets", []) or []:
        if bucket.get("bucket") == name:
            return bucket
    return {}


# ---------------------------------------------------------------- slides

def slide_1_scorecard(deck, coverage, focus):
    """Where I am today. Leadership's first question is always 'what is the number'."""
    slide = deck.slide()
    totals = coverage.get("totals", {})
    b1 = bucket_of(coverage, "Bucket 1")
    b2 = bucket_of(coverage, "Bucket 2")

    deck.text(slide, MARGIN, Inches(0.52), W - 2 * MARGIN, Inches(0.28),
              "FY27 H1 \u00b7 TERRITORY PLAN \u00b7 INDIA", size=11, color=ACCENT,
              bold=True, space=True)
    deck.text(slide, MARGIN, Inches(0.86), W - 2 * MARGIN, Inches(0.62),
              "Where I am, and how I make the number", size=32, color=WHITE, bold=True)
    deck.fill(slide, MARGIN, Inches(1.62), Inches(1.6), Inches(0.04), ACCENT)

    def bucket_card(x, bucket, color):
        w = Inches(6.0)
        h = Inches(2.2)
        deck.fill(slide, x, Inches(1.95), w, h, PANEL, line=LINE, radius=True)
        deck.text(slide, Emu(int(x + Inches(0.3))), Inches(2.16), Emu(int(w - Inches(0.6))),
                  Inches(0.26), bucket.get("label", "").upper(), size=10.5, color=color,
                  bold=True, space=True)
        attained = bucket.get("attainedH1") or 0
        deck.text(slide, Emu(int(x + Inches(0.3))), Inches(2.5), Inches(2.4), Inches(0.6),
                  money(attained), size=34, color=WHITE, bold=True)
        target = bucket.get("h1Target")
        if bucket.get("targetKnown"):
            right = "of %s H1 target" % money(target)
            sub = "%s to go \u00b7 %.0f%% attained" % (money(bucket.get("gap")),
                                                       bucket.get("attainmentPct") or 0)
        else:
            right = "H1 target: TBD"
            sub = "target not yet set \u2014 attainment shown as absolute"
        deck.text(slide, Emu(int(x + Inches(2.85))), Inches(2.72), Emu(int(w - Inches(3.15))),
                  Inches(0.3), right, size=12.5, color=MUTED)
        deck.text(slide, Emu(int(x + Inches(0.3))), Inches(3.18), Emu(int(w - Inches(0.6))),
                  Inches(0.28), sub, size=11, color=MUTED)

        # Progress bar. A number without a denominator is a claim; a bar is a position.
        bar_w = w - Inches(0.6)
        deck.fill(slide, Emu(int(x + Inches(0.3))), Inches(3.56), bar_w, Inches(0.16), PANEL_2)
        if bucket.get("targetKnown") and target:
            filled = max(0.02, min(1.0, float(attained) / float(target)))
            deck.fill(slide, Emu(int(x + Inches(0.3))), Inches(3.56),
                      Emu(int(bar_w * filled)), Inches(0.16), color)
        return h

    bucket_card(MARGIN, b1, ACCENT)
    bucket_card(Inches(6.95), b2, PLAY_COLOR["Innovate"])

    ftotals = focus.get("totals", {})
    cards = [
        ("Focus accounts", num(focus.get("selectedCount")), "of %s in book" % num(focus.get("bookSize"))),
        ("Potential ARR H1", money(ftotals.get("potentialArr")), "sized, new business"),
        ("Current ARR", money(ftotals.get("currentArr")), "installed base in focus set"),
        ("Live H1 pipeline", money(ftotals.get("h1Pipeline")), "net-new, close-dated in H1"),
    ]
    x = MARGIN
    for label, value, sub in cards:
        deck.card(slide, x, Inches(4.42), Inches(2.95), Inches(1.32), label, value, sub)
        x += Inches(3.11)

    deck.text(slide, MARGIN, Inches(6.06), W - 2 * MARGIN, Inches(0.5),
              "Bucket 1 is GHE + GHAS. Bucket 2 is consumption \u2014 Copilot, AI credits, "
              "Actions, Codespaces, Code Quality. Targets and attainment are net-new; "
              "renewals are tracked separately and shown on the coverage slide.",
              size=11.5, color=MUTED)
    deck.footnote(slide, "Attainment as of Q1 to date. All figures computed from SuperDash, "
                         "Kusto billing facts and Salesforce - none entered by hand.")
    return slide


def slide_2_learnings(deck, learnings):
    slide = deck.slide("What H2 FY26 taught me, and what changes",
                       "Carry-forward",
                       note="Each learning is derived from a count in the run data, not from "
                            "recollection. The right-hand column is the behaviour change, which "
                            "is the part that matters.")
    rows = []
    colors = {}
    for index, item in enumerate(learnings.get("learnings", [])[:5]):
        rows.append([
            truncate(item.get("headline", ""), 42),
            truncate(item.get("detail", ""), 118),
            truncate(item.get("carryForward", ""), 76),
        ])
        colors[index] = WARN if index < 3 else ACCENT

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Learning", "What the record shows", "What I do differently in H1"],
               [3.0, 6.2, 4.1], rows, row_h=0.92, size=11, colors=colors)

    deck.footnote(slide, "Derived from focus-accounts.json, coverage.json and Salesforce open "
                         "opportunity records - every figure above is reproducible.")
    return slide


def slide_3_portfolio(deck, focus, coverage):
    slide = deck.slide("The book, split three ways", "Portfolio by play",
                       note="Play assignment comes from the account's own product footprint and "
                            "whitespace, not from preference. TPID accounts are run with "
                            "Microsoft and a partner by default.")
    accounts = focus.get("accounts", [])

    by_play = {p: [] for p in PLAYS}
    for account in accounts:
        if account.get("play") in by_play:
            by_play[account["play"]].append(account)

    x = MARGIN
    col_w = Inches(4.02)
    for play in PLAYS:
        rows = by_play[play]
        value = sum(float(r.get("potentialArr") or 0) for r in rows)
        overlap = sum(1 for r in rows if r.get("msftOverlap"))
        color = PLAY_COLOR[play]

        deck.fill(slide, x, BODY_TOP, col_w, Inches(4.5), PANEL, line=LINE, radius=True)
        deck.fill(slide, x, BODY_TOP, col_w, Inches(0.06), color)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(0.26))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.32), play.upper(),
                  size=13, color=color, bold=True, space=True)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(0.62))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.5),
                  "%s accounts \u00b7 %s" % (len(rows), money(value)),
                  size=19, color=WHITE, bold=True)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(1.06))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.56),
                  PLAY_THESIS[play], size=11, color=MUTED)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(1.72))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.26),
                  "%d WITH MICROSOFT TPID \u00b7 CO-SELL" % overlap,
                  size=9.5, color=color, bold=True, space=True)

        top = sorted(rows, key=lambda r: -float(r.get("potentialArr") or 0))[:6]
        cursor = float(BODY_TOP + Inches(2.08))
        for account in top:
            flag = " \u25c6" if account.get("msftOverlap") else ""
            deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(cursor)),
                      Emu(int(col_w - Inches(1.5))), Inches(0.28),
                      truncate(account.get("name", ""), 28) + flag, size=10.5, color=TEXT)
            deck.text(slide, Emu(int(x + col_w - Inches(1.24))), Emu(int(cursor)),
                      Inches(0.98), Inches(0.28), money(account.get("potentialArr")),
                      size=10.5, color=color, bold=True, align=PP_ALIGN.RIGHT)
            cursor += Inches(0.33)
        if len(rows) > 6:
            deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(cursor + Inches(0.04))),
                      Emu(int(col_w - Inches(0.52))), Inches(0.26),
                      "+%d more" % (len(rows) - 6), size=10, color=MUTED)
        x += Inches(4.18)

    deck.text(slide, MARGIN, Inches(6.32), W - 2 * MARGIN, Inches(0.3),
              "\u25c6 = Microsoft TPID present \u2192 run as co-sell with the Microsoft account "
              "team and a delivery partner. %d of %d focus accounts qualify."
              % (focus.get("totals", {}).get("withMsftOverlap", 0), len(accounts)),
              size=11, color=MUTED)
    deck.footnote(slide, "Top six by sized potential shown per play; full list in the evidence "
                         "workbook.")
    return slide


def slide_4_key_accounts(deck, focus):
    slide = deck.slide("Key accounts: the must-wins", "Q1 \u00b7 Key accounts",
                       note="Ranked on potential 40 / live pipeline 20 / two-way communication 20 "
                            "/ dated trigger 20. Every 'why now' below is a cited, dated public "
                            "event or an open Salesforce opportunity.")
    accounts = focus.get("accounts", [])
    tier1 = [a for a in accounts if (a.get("tier") or "").startswith("Tier 1")][:10]

    rows, colors = [], {}
    for index, account in enumerate(tier1):
        triggers = account.get("triggers") or []
        why = triggers[0].get("headline") if triggers else ""
        if not why and float(account.get("h1PipelineValue") or 0) > 0:
            why = "Open H1 opportunity \u00b7 %s" % (account.get("bestStage") or "in stage")
        pipeline = float(account.get("h1PipelineValue") or 0)
        rows.append([
            truncate(account.get("name", ""), 26),
            account.get("play", ""),
            money(account.get("potentialArr")),
            money(pipeline) if pipeline else "\u2014",
            "Yes" if account.get("msftOverlap") else "\u2014",
            truncate(why, 62),
        ])
        colors[index] = PLAY_COLOR.get(account.get("play"), ACCENT)

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Account", "Play", "Potential ARR", "Live H1 pipe", "MSFT", "Why now"],
               [2.6, 1.3, 1.5, 1.4, 0.8, 5.4], rows, row_h=0.44, size=11, colors=colors)

    bottom = float(BODY_TOP) + Inches(0.3) + Inches(0.44) * len(rows) + Inches(0.24)
    total = sum(float(a.get("potentialArr") or 0) for a in tier1)
    deck.text(slide, MARGIN, Emu(int(bottom)), W - 2 * MARGIN, Inches(0.34),
              "%d must-win accounts carry %s of sized potential \u2014 %s of the focus set total."
              % (len(tier1), money(total),
                 "%.0f%%" % (100.0 * total / max(1.0, float(focus.get("totals", {}).get("potentialArr") or 1)))),
              size=12, color=TEXT)
    deck.footnote(slide, "Tier 2 and Tier 3 accounts are worked to the same plays on a lighter "
                         "cadence; the full 40 are in the evidence workbook.")
    return slide


def slide_5_the_number(deck, potential, focus, coverage):
    slide = deck.slide("What the half is worth", "Q3 \u00b7 The number",
                       note="Copilot is sized on seats without Copilot today. GHAS is sized per "
                            "active committer because that is how it bills. GHE is Azure DevOps "
                            "TAM available to migrate. AI credits already invoiced are existing "
                            "revenue and are excluded from potential.")
    accounts = focus.get("accounts", [])
    aiu = potential.get("aiuTotals", {})

    quantities = {"Copilot": 0, "GHAS": 0, "GHE": 0}
    values = {"Copilot": 0.0, "GHAS": 0.0, "GHE": 0.0}
    for account in accounts:
        for line in account.get("lines", []):
            product = line.get("product")
            if product in values:
                values[product] += float(line.get("value") or 0)
                quantities[product] += int(line.get("quantity") or 0)

    cards = [
        ("Copilot seats", num(quantities["Copilot"]), money(values["Copilot"]),
         PLAY_COLOR["Innovate"]),
        ("GHAS committers", num(quantities["GHAS"]), money(values["GHAS"]), PLAY_COLOR["Trust"]),
        ("GHE seats", num(quantities["GHE"]), money(values["GHE"]), PLAY_COLOR["Scale"]),
        ("AI credits / yr", num(aiu.get("currentAnnualisedCredits")),
         "%s invoiced run-rate" % money(aiu.get("currentAnnualisedSpend")), ACCENT),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, BODY_TOP, Inches(2.95), Inches(1.42), label, value, sub, color)
        x += Inches(3.11)

    rows = [
        ["Copilot", "Bucket 2", "Seats with no Copilot today", num(quantities["Copilot"]),
         money(values["Copilot"])],
        ["GHAS", "Bucket 1", "Active committers L90d not covered", num(quantities["GHAS"]),
         money(values["GHAS"])],
        ["GHE", "Bucket 1", "Azure DevOps seats available to migrate", num(quantities["GHE"]),
         money(values["GHE"])],
        ["AI credits", "Bucket 2", "Accounts consuming credits today",
         num(aiu.get("accountsConsumingAiu")), money(aiu.get("currentAnnualisedSpend")) + " run-rate"],
    ]
    colors = {0: PLAY_COLOR["Innovate"], 1: PLAY_COLOR["Trust"],
              2: PLAY_COLOR["Scale"], 3: ACCENT}
    deck.table(slide, MARGIN, Inches(3.42), W - 2 * MARGIN,
               ["Product", "Bucket", "Sizing basis", "Quantity", "Sized ARR"],
               [1.6, 1.3, 6.2, 1.6, 1.8], rows, row_h=0.46, size=11.5, colors=colors)

    total = sum(values.values())
    deck.text(slide, MARGIN, Inches(5.66), W - 2 * MARGIN, Inches(0.34),
              "Total sized potential across the focus set: %s. This is addressable, not "
              "committed \u2014 the next slide shows how much of it the targets actually need."
              % money(total), size=12.5, color=TEXT)
    deck.footnote(slide, "Pricing is observed-first: where an account already buys a product its "
                         "own billed rate is used; otherwise list price. GHE alone is derived.")
    return slide


def slide_6_coverage(deck, coverage, focus):
    slide = deck.slide("Coverage: target vs live pipeline vs sized TAM",
                       "Q4 \u00b7 Coverage math",
                       note="Three separate columns on purpose. Sized TAM is not commit. GHE is "
                            "under-covered on net-new and needs migration supply. GHAS is 25x "
                            "covered by TAM but consumed by only two accounts, so the constraint "
                            "is motion, not opportunity.")
    rows, colors = [], {}
    pipeline = coverage.get("pipeline", {})

    for index, product in enumerate(coverage.get("products", []) or []):
        known = product.get("targetKnown")
        ratio = product.get("coverageRatio")
        rows.append([
            product.get("product", ""),
            product.get("bucket", ""),
            money(product.get("q1Target")) if known else "TBD",
            money(product.get("q2Target")) if known else "TBD",
            money(product.get("h1Target")) if known else "TBD",
            money(product.get("sizedPotential")),
            ("%.2fx" % ratio) if ratio is not None else "\u2014",
        ])
        colors[index] = ratio_color(ratio)

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Product", "Bucket", "Q1 target", "Q2 target", "H1 target",
                "Sized TAM in focus set", "Coverage"],
               [1.6, 1.6, 1.5, 1.5, 1.5, 3.4, 1.4], rows, row_h=0.46, size=11.5,
               colors=colors)

    top = float(BODY_TOP) + Inches(0.3) + Inches(0.46) * len(rows) + Inches(0.32)

    cards = [
        ("Live H1 net-new", money(pipeline.get("netNew")),
         "%d accounts, close-dated in H1" % (pipeline.get("accounts") or 0), ACCENT),
        ("H1 renewal pipeline", money(pipeline.get("renewal")),
         "excluded from target attainment", MUTED),
        ("Stale pipeline", money(pipeline.get("stale")),
         "%d records past close date" % (pipeline.get("staleCount") or 0), WARN),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, Emu(int(top)), Inches(3.98), Inches(1.3), label, value, sub, color)
        x += Inches(4.14)

    products = {p.get("product"): p for p in coverage.get("products", []) or []}
    ghe_ratio = (products.get("GHE") or {}).get("coverageRatio")
    ghas_ratio = (products.get("GHAS") or {}).get("coverageRatio")
    ghas_consuming = sum(
        1 for a in focus.get("accounts", [])
        if float(((a.get("current") or {}).get("consumptionObserved") or {}).get("ghas") or 0) > 1
    )

    if ghe_ratio is None or ghas_ratio is None:
        narrative = ("Targets are not yet set for every product, so coverage reads TBD. Sized TAM "
                     "is what the focus set can address, not what is committed - fill in "
                     "targets.json and re-run to see the coverage gap per product.")
    else:
        narrative = ("GHE is the real constraint: %.2fx coverage means the installed book does not "
                     "contain enough GHE to reach the H1 number on conversion alone - it needs "
                     "migration supply and new logos. GHAS is the inverse: %.0fx TAM but only %d "
                     "consuming account%s, so the constraint is motion, not opportunity."
                     % (ghe_ratio, ghas_ratio, ghas_consuming,
                        "" if ghas_consuming == 1 else "s"))

    deck.text(slide, MARGIN, Emu(int(top + Inches(1.52))), W - 2 * MARGIN, Inches(0.68),
              narrative, size=12, color=TEXT)
    deck.footnote(slide, "Targets are net-new. Renewal pipeline is shown for context only and "
                         "does not count towards attainment.")
    return slide


def slide_7_how(deck, focus, report):
    slide = deck.slide("How I get there", "Q4 \u00b7 Execution plan",
                       note="This is the slide that answers the question leadership actually "
                            "cares about. Each play has a named motion, a named set of accounts "
                            "and a quarter. Q1 accounts are already in motion.")
    accounts = focus.get("accounts", [])
    by_play = {p: [] for p in PLAYS}
    for account in accounts:
        if account.get("play") in by_play:
            by_play[account["play"]].append(account)

    motions = {
        "Innovate": [
            "Copilot value review on the installed base \u2014 usage evidence, not a pitch",
            "Convert AI credit consumption into committed seat expansion",
            "Executive AI briefing where a trigger gives a reason to convene",
        ],
        "Trust": [
            "Committer-base audit \u2192 GHAS trial on the largest active repo set",
            "Secret-scanning finding as the wedge into a security-owner conversation",
            "Compliance and audit framing for regulated accounts",
        ],
        "Scale": [
            "Azure DevOps migration assessment with Microsoft co-sell",
            "Toolchain consolidation economics at renewal",
            "Partner-delivered migration to remove the services constraint",
        ],
    }

    x = MARGIN
    col_w = Inches(4.02)
    for play in PLAYS:
        rows = sorted(by_play[play], key=lambda r: -float(r.get("potentialArr") or 0))
        color = PLAY_COLOR[play]
        q1 = [r for r in rows if (r.get("tier") or "").startswith(("Tier 1", "Tier 2"))][:4]
        q2 = [r for r in rows if r not in q1][:3]

        deck.fill(slide, x, BODY_TOP, col_w, Inches(4.62), PANEL, line=LINE, radius=True)
        deck.fill(slide, x, BODY_TOP, col_w, Inches(0.06), color)
        deck.text(slide, Emu(int(x + Inches(0.24))), Emu(int(BODY_TOP + Inches(0.24))),
                  Emu(int(col_w - Inches(0.48))), Inches(0.3),
                  "%s \u00b7 %s" % (play.upper(), money(sum(float(r.get("potentialArr") or 0)
                                                            for r in rows))),
                  size=12, color=color, bold=True, space=True)
        deck.bullets(slide, Emu(int(x + Inches(0.24))), Emu(int(BODY_TOP + Inches(0.64))),
                     Emu(int(col_w - Inches(0.48))), motions[play], size=10.5, gap=0.1,
                     bullet_color=color)

        cursor = float(BODY_TOP + Inches(2.34))
        for label, group in (("Q1 \u00b7 IN MOTION", q1), ("Q2 \u00b7 BUILD", q2)):
            deck.text(slide, Emu(int(x + Inches(0.24))), Emu(int(cursor)),
                      Emu(int(col_w - Inches(0.48))), Inches(0.24), label,
                      size=9, color=MUTED, bold=True, space=True)
            cursor += Inches(0.28)
            for account in group:
                deck.text(slide, Emu(int(x + Inches(0.24))), Emu(int(cursor)),
                          Emu(int(col_w - Inches(1.4))), Inches(0.26),
                          truncate(account.get("name", ""), 26), size=10, color=TEXT)
                deck.text(slide, Emu(int(x + col_w - Inches(1.16))), Emu(int(cursor)),
                          Inches(0.92), Inches(0.26), money(account.get("potentialArr")),
                          size=10, color=color, bold=True, align=PP_ALIGN.RIGHT)
                cursor += Inches(0.26)
            cursor += Inches(0.12)
        x += Inches(4.18)

    deck.footnote(slide, "Motions are drawn from the GitHub Product Adoption Framework key "
                         "actions for each play. Account sequencing follows the composite rank.")
    return slide


def slide_8_msft_partners(deck, focus, partners):
    slide = deck.slide("Microsoft overlap and partner leverage", "Q5 \u00b7 Co-sell",
                       note="A TPID means the account is already a Microsoft customer with a "
                            "named account team. That is a route in, and it is also how partner "
                            "delivery capacity gets funded.")
    accounts = focus.get("accounts", [])
    overlap = [a for a in accounts if a.get("msftOverlap")]
    partner_map = (partners or {}).get("accounts", {}) or {}

    with_partner = [a for a in accounts
                    if [p for p in (partner_map.get(a.get("salesforceId"), {}) or {}).get("partners", [])
                        if p.get("name") and p.get("name") != "Invalid"]]

    cards = [
        ("Accounts with TPID", num(len(overlap)),
         "%s of focus set" % ("%.0f%%" % (100.0 * len(overlap) / max(1, len(accounts)))), ACCENT),
        ("Potential under co-sell", money(sum(float(a.get("potentialArr") or 0) for a in overlap)),
         "addressable with Microsoft", WHITE),
        ("Accounts with a named partner", num(len(with_partner)),
         "existing partner relationship", PLAY_COLOR["Scale"]),
        ("Partner-led delivery need", num(len([a for a in overlap if a.get("play") == "Scale"])),
         "Scale accounts needing migration services", PLAY_COLOR["Trust"]),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, BODY_TOP, Inches(2.95), Inches(1.42), label, value, sub, color)
        x += Inches(3.11)

    top_overlap = sorted(overlap, key=lambda a: -float(a.get("potentialArr") or 0))[:7]
    rows, colors = [], {}
    for index, account in enumerate(top_overlap):
        entry = partner_map.get(account.get("salesforceId"), {}) or {}
        names = [p.get("name") for p in (entry.get("partners") or [])
                 if p.get("name") and p.get("name") != "Invalid"]
        rows.append([
            truncate(account.get("name", ""), 26),
            account.get("play", ""),
            money(account.get("potentialArr")),
            (account.get("tpids") or [""])[0],
            truncate(", ".join(names) if names else "No partner mapped \u2014 needs sourcing", 46),
        ])
        colors[index] = PLAY_COLOR.get(account.get("play"), ACCENT)

    deck.table(slide, MARGIN, Inches(3.42), W - 2 * MARGIN,
               ["Account", "Play", "Potential ARR", "Microsoft TPID", "Partner"],
               [2.8, 1.3, 1.6, 2.0, 4.4], rows, row_h=0.36, size=10.5, colors=colors)

    deck.text(slide, MARGIN, Inches(6.4), W - 2 * MARGIN, Inches(0.42),
              "How I use it: TPID accounts get a joint account-team introduction before any "
              "GitHub-only outreach; Scale accounts get a partner attached to the migration "
              "before the technical win, so delivery is never the reason a deal slips.",
              size=11.5, color=MUTED)
    deck.footnote(slide, "TPIDs from Salesforce MSFT_All_TPIDs__c / MS_Sales_TPID_Best_Match__c. "
                         "Partner relationships from Salesforce Partner records.")
    return slide


def slide_9_working(deck, learnings):
    slide = deck.slide("What's working, what's not", "Q6 \u00b7 Honest read",
                       note="Both columns are counts from the run data. The right-hand column is "
                            "where the asks on the next slide come from.")
    working = ["%s \u2014 %s" % (w.get("point"), w.get("proof"))
               for w in learnings.get("working", [])]
    not_working = ["%s \u2014 %s" % (w.get("point"), w.get("proof"))
                   for w in learnings.get("notWorking", [])]

    deck.panel(slide, MARGIN, BODY_TOP, Inches(6.0), "WHAT'S WORKING", working,
               GOOD, size=12, gap=0.2, min_h=Inches(4.4))
    deck.panel(slide, Inches(6.95), BODY_TOP, Inches(6.0), "WHAT'S NOT", not_working,
               WARN, size=12, gap=0.2, min_h=Inches(4.4))

    deck.text(slide, MARGIN, Inches(6.3), W - 2 * MARGIN, Inches(0.4),
              "The pattern: I can open accounts, and the installed base is real. What I cannot "
              "yet do at scale is convert opening into dated, forecastable pipeline \u2014 which "
              "is exactly what the asks address.", size=12, color=TEXT)
    deck.footnote(slide, "Every figure computed from the focus set; none estimated.")
    return slide


def slide_10_asks(deck, coverage, focus, learnings):
    slide = deck.slide("Asks", "Q7 \u00b7 Leadership and cross-functional",
                       note="Each ask is tied to a specific number on an earlier slide, so it is "
                            "answerable rather than aspirational.")
    facts = learnings.get("facts", {})
    products = {p.get("product"): p for p in coverage.get("products", []) or []}
    ghe = products.get("GHE", {})
    ghas = products.get("GHAS", {})

    leadership = []
    if ghe.get("targetKnown"):
        leadership.append(
            "GHE supply: sized GHE potential is %s against a %s H1 target (%.2fx). I need "
            "migration-led demand generation or account additions to close the supply gap, not "
            "just conversion pressure." % (money(ghe.get("sizedPotential")),
                                           money(ghe.get("h1Target")),
                                           ghe.get("coverageRatio") or 0))
    else:
        leadership.append(
            "GHE target: not yet set. Sized GHE potential in the focus set is %s - I need the "
            "number so I can tell you whether that is coverage or a supply gap."
            % money(ghe.get("sizedPotential")))

    consumption = products.get("Consumption") or {}
    if not consumption.get("targetKnown"):
        leadership.append(
            "Bucket 2 target: consumption target is still unset. I need the number to plan "
            "against \u2014 sized consumption potential in the focus set is %s."
            % money(consumption.get("sizedPotential")))

    leadership.append(
        "GHAS technical capacity: %d of %d focus accounts consume GHAS today against %s of "
        "committer-based TAM. Converting that needs security-specialist time, not more "
        "pipeline." % (facts.get("consumingAccounts", {}).get("ghas", 0),
                       facts.get("focusCount", 0), money(ghas.get("sizedPotential"))))

    xfn = [
        "Partnerships: %d focus accounts carry a Microsoft TPID but only %d have a named "
        "partner. I need partner sourcing on the Scale accounts so migration delivery is not "
        "the constraint." % (facts.get("withOverlap", 0), facts.get("withNamedPartner", 0)),
        "Microsoft co-sell: joint account planning on the %d TPID accounts, sequenced before "
        "Q2 so the Q2 number has a Q1 origin." % facts.get("withOverlap", 0),
        "Marketing / SDR: %d of %d focus accounts have no two-way contact. Targeted demand "
        "generation into those accounts is faster than cold outbound from me."
        % (facts.get("withoutTwoWay", 0), facts.get("focusCount", 0)),
        "Deal desk / ops: %d stale opportunities worth %s need a hygiene pass so forecast "
        "coverage means something." % (facts.get("staleCount", 0),
                                       money(facts.get("staleValue"))),
    ]

    deck.panel(slide, MARGIN, BODY_TOP, Inches(6.0), "FROM LEADERSHIP", leadership,
               ACCENT, size=11.5, gap=0.2, min_h=Inches(4.5))
    deck.panel(slide, Inches(6.95), BODY_TOP, Inches(6.0), "FROM CROSS-FUNCTIONAL PARTNERS",
               xfn, PLAY_COLOR["Scale"], size=11.5, gap=0.2, min_h=Inches(4.5))

    b1_gap = bucket_of(coverage, "Bucket 1").get("gap")
    commitment = (
        "Commitment: %s of Bucket 1 gap closed across H1, worked through %d focus accounts "
        "carrying %s of sized potential." % (money(b1_gap), focus.get("selectedCount", 0),
                                             money(focus.get("totals", {}).get("potentialArr")))
        if b1_gap else
        "Commitment: %d focus accounts carrying %s of sized potential, worked to the plan on "
        "the previous slides." % (focus.get("selectedCount", 0),
                                  money(focus.get("totals", {}).get("potentialArr")))
    )
    deck.text(slide, MARGIN, Inches(6.4), W - 2 * MARGIN, Inches(0.36),
              commitment, size=12.5, color=WHITE, bold=True)
    return slide


# ---------------------------------------------------------------- entry

def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: exec_deck.py <runDir> <out.pptx>")
    run_dir, out_path = sys.argv[1], sys.argv[2]

    focus = load(run_dir, "focus-accounts.json")
    potential = load(run_dir, "potential.json", {})
    coverage = load(run_dir, "coverage.json", {})
    learnings = load(run_dir, "learnings.json", {})
    partners = load(run_dir, "partners.json", {})
    report = load(run_dir, "fy27-territory-plan.json", {})
    if not focus:
        raise SystemExit("Cannot read focus-accounts.json - run rank.py stage2 first")

    # Partner counts are needed by the asks slide but are computed on slide 8, so derive
    # the one figure the asks reference here rather than duplicating the join.
    partner_map = (partners or {}).get("accounts", {}) or {}
    named_partners = sum(
        1 for a in focus.get("accounts", [])
        if [p for p in (partner_map.get(a.get("salesforceId"), {}) or {}).get("partners", [])
            if p.get("name") and p.get("name") != "Invalid"]
    )
    learnings.setdefault("facts", {})["withNamedPartner"] = named_partners

    deck = Deck()
    slide_1_scorecard(deck, coverage, focus)
    slide_2_learnings(deck, learnings)
    slide_3_portfolio(deck, focus, coverage)
    slide_4_key_accounts(deck, focus)
    slide_5_the_number(deck, potential, focus, coverage)
    slide_6_coverage(deck, coverage, focus)
    slide_7_how(deck, focus, report)
    slide_8_msft_partners(deck, focus, partners)
    slide_9_working(deck, learnings)
    slide_10_asks(deck, coverage, focus, learnings)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    deck.save(out_path)
    print(json.dumps({"deckPath": out_path, "slides": len(deck.prs.slides._sldIdLst)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
