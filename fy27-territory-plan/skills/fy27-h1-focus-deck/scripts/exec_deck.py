#!/usr/bin/env python3
"""FY27 H1 leadership deck - the 30-minute executive cut.

Eleven slides: the seven questions leadership asked, plus a carry-forward slide and a
live-deals slide, and nothing else. The long deck (deck.py) remains the evidence pack;
this is what gets presented. Theme and layout
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

# Slide 2 renders one row per learning. Six wrapped rows is what fits between BODY_TOP
# and the footnote; adding a seventh needs the row height revisited, not this bumped.
LEARNING_ROWS = 6

# Same constraint on the key-deals table: seven wrapped rows fit above the footnote.
KEY_DEAL_ROWS = 7

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
            sub = "target not yet set \u2014 attainment absolute"
        deck.text(slide, Emu(int(x + Inches(2.85))), Inches(2.72), Emu(int(w - Inches(3.15))),
                  Inches(0.3), right, size=12.5, color=MUTED)
        # Pipeline belongs inside its own bucket panel. Shown as one blended figure it
        # reads as cover for whichever gap it happens to sit next to.
        live = bucket.get("livePipeline") or 0
        if live:
            sub = "%s \u00b7 %s live pipeline" % (sub, money(live))
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
    b1_pipe = (coverage.get("pipeline", {}) or {}).get("byBucket", {}).get("Bucket 1")
    cards = [
        ("Focus accounts", num(focus.get("selectedCount")), "of %s in book" % num(focus.get("bookSize"))),
        ("In two-way comms", num(ftotals.get("withTwoWay")),
         "of %s focus accounts" % num(focus.get("selectedCount"))),
        ("Current ARR", money(ftotals.get("currentArr")), "installed base in focus set"),
        ("Bucket 1 pipeline", money(b1_pipe), "GHE + GHAS, close-dated in H1"),
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
    items = learnings.get("learnings", [])[:LEARNING_ROWS]
    for index, item in enumerate(items):
        rows.append([
            item.get("headline", ""),
            item.get("detail", ""),
            item.get("carryForward", ""),
        ])
        colors[index] = WARN if index < 3 else ACCENT

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Learning", "What the record shows", "What I do differently in H1"],
               [3.0, 6.2, 4.1], rows, row_h=0.62, size=10.5, colors=colors, wrap=True)

    deck.footnote(slide, "Derived from focus-accounts.json, coverage.json and Salesforce open "
                         "opportunity records - every figure above is reproducible.")
    return slide


def slide_3_key_deals(deck, focus, crm=None, report=None):
    """The deals themselves, not the accounts that hold them.

    Selection is deterministic: every dated, non-renewal H1 opportunity in the book,
    ranked by value, top KEY_DEAL_ROWS. Nothing here is hand-picked, so the slide
    cannot quietly become a curated list that flatters the pipeline.

    Deliberately sourced from the whole book rather than the focus 40. A live deal is
    a live deal regardless of where its account ranks, and the ranking model scores
    modelled whitespace - so an account that has already committed seats can rank low
    while carrying one of the largest deals on the desk. Scoping this slide to the
    focus set would hide exactly those deals.
    """
    slide = deck.slide("Key deals in play", "Live deals",
                       note="Every open, dated, non-renewal H1 opportunity in the book, "
                            "largest first. Renewals are excluded - they are not new "
                            "revenue against these targets.")
    plays = {}
    for row in (report or {}).get("accounts", []):
        sid = row.get("salesforceId")
        if sid:
            plays[sid] = row.get("primaryPlay", "")
    accounts = {}
    for account in focus.get("accounts", []):
        sid = account.get("salesforceId")
        if sid:
            accounts[sid] = account
    deals = []
    seen = set()
    sources = [(a.get("salesforceId"), a, a.get("openPipeline") or [])
               for a in focus.get("accounts", [])]
    for sid, row in ((crm or {}).get("accounts", {}) or {}).items():
        if sid in accounts:
            continue
        sources.append((sid, {"name": row.get("name", ""),
                              "play": plays.get(sid, ""),
                              "salesforceId": sid}, row.get("openPipeline") or []))
    for sid, account, pipeline in sources:
        for opp in pipeline:
            if not opp.get("inH1") or opp.get("isRenewal"):
                continue
            amount = float(opp.get("amount") or 0)
            if amount <= 0:
                continue
            token = (sid, opp.get("name"), amount)
            if token in seen:
                continue
            seen.add(token)
            deals.append((amount, account, opp))
    deals.sort(key=lambda d: -d[0])
    top = deals[:KEY_DEAL_ROWS]

    focus_ids = set(accounts)
    rows, colors = [], {}
    outside_value = 0.0
    outside_names = []
    for index, (amount, account, opp) in enumerate(top):
        scenario = opp.get("note") or ""
        if not scenario:
            close = str(opp.get("closeDate") or "")
            scenario = "%s%s" % (opp.get("stage") or "In stage",
                                 (" \u00b7 close %s" % close) if close else "")
        sid = account.get("salesforceId")
        outside = sid not in focus_ids
        if outside:
            outside_value += amount
            outside_names.append(account.get("name", ""))
        rows.append([
            account.get("name", "") + (" *" if outside else ""),
            account.get("play", ""),
            opp.get("product") or "\u2014",
            money(amount),
            opp.get("stage") or "\u2014",
            scenario,
        ])
        colors[index] = PLAY_COLOR.get(account.get("play"), ACCENT)

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Account", "Play", "Product", "Deal size", "Stage", "Where it stands"],
               [2.5, 1.2, 1.3, 1.3, 1.6, 5.4], rows, row_h=0.44, size=10.5,
               colors=colors, wrap=True)

    total = sum(d[0] for d in deals)
    shown = sum(d[0] for d in top)
    seller = sum(d[0] for d in deals if (d[2].get("source") == "seller"))
    note = ("%d open H1 deals worth %s in total; the %d largest are shown (%s). "
            "%s is seller-sourced and not yet raised in Salesforce. Renewals excluded."
            % (len(deals), money(total), len(top), money(shown), money(seller)))
    if outside_names:
        note += (" * %s sits outside the focus 40, so its %s is excluded from the "
                 "coverage figures on the target slides - those count focus accounts "
                 "only." % (" and ".join(outside_names), money(outside_value)))
    deck.footnote(slide, note)
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
            money(pipeline) if pipeline else "\u2014",
            "Yes" if account.get("msftOverlap") else "\u2014",
            truncate(why, 62),
        ])
        colors[index] = PLAY_COLOR.get(account.get("play"), ACCENT)

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Account", "Play", "Live H1 pipe", "MSFT", "Why now"],
               [2.9, 1.4, 1.5, 0.9, 6.3], rows, row_h=0.44, size=11, colors=colors)

    bottom = float(BODY_TOP) + Inches(0.3) + Inches(0.44) * len(rows) + Inches(0.24)
    two_way = sum(1 for a in tier1 if a.get("twoWay"))
    with_pipe = sum(1 for a in tier1 if float(a.get("h1PipelineValue") or 0) > 0)
    with_tpid = sum(1 for a in tier1 if a.get("msftOverlap"))
    deck.text(slide, MARGIN, Emu(int(bottom)), W - 2 * MARGIN, Inches(0.34),
              "%d must-wins \u00b7 %d in two-way comms \u00b7 %d with a dated H1 deal \u00b7 "
              "%d co-sellable through a Microsoft TPID."
              % (len(tier1), two_way, with_pipe, with_tpid), size=11.5, color=TEXT)
    deck.footnote(slide, "Tier 2 and Tier 3 accounts are worked to the same plays on a lighter "
                         "cadence; the full 40 are in the evidence workbook.")
    return slide


def slide_5_portfolio(deck, focus, coverage):
    slide = deck.slide("The book, split three ways", "Q2 \u00b7 Key plays",
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
        pipe = sum(float(r.get("h1PipelineValue") or 0) for r in rows)
        engaged = sum(1 for r in rows if r.get("twoWay"))
        overlap = sum(1 for r in rows if r.get("msftOverlap"))
        color = PLAY_COLOR[play]

        deck.fill(slide, x, BODY_TOP, col_w, Inches(4.5), PANEL, line=LINE, radius=True)
        deck.fill(slide, x, BODY_TOP, col_w, Inches(0.06), color)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(0.26))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.32), play.upper(),
                  size=13, color=color, bold=True, space=True)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(0.62))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.5),
                  "%s accounts \u00b7 %s live" % (len(rows), money(pipe) if pipe else "no"),
                  size=19, color=WHITE, bold=True)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(1.06))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.56),
                  PLAY_THESIS[play], size=11, color=MUTED)
        deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(BODY_TOP + Inches(1.72))),
                  Emu(int(col_w - Inches(0.52))), Inches(0.26),
                  "%d IN TWO-WAY COMMS \u00b7 %d WITH MICROSOFT TPID"
                  % (engaged, overlap),
                  size=9.5, color=color, bold=True, space=True)

        top = sorted(rows, key=lambda r: int(r.get("rank") or 999))[:6]
        cursor = float(BODY_TOP + Inches(2.08))
        for account in top:
            flag = " \u25c6" if account.get("msftOverlap") else ""
            deck.text(slide, Emu(int(x + Inches(0.26))), Emu(int(cursor)),
                      Emu(int(col_w - Inches(1.5))), Inches(0.28),
                      truncate(account.get("name", ""), 28) + flag, size=10.5, color=TEXT)
            deck.text(slide, Emu(int(x + col_w - Inches(1.24))), Emu(int(cursor)),
                      Inches(0.98), Inches(0.28), "#%d" % int(account.get("rank") or 0),
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
    deck.footnote(slide, "Top six by composite rank shown per play; full list in the evidence "
                         "workbook.")
    return slide


def slide_6_the_number(deck, potential, focus, coverage):
    slide = deck.slide("What the half is worth", "Q3 \u00b7 The number",
                       note="Copilot is sized on seats without Copilot today. GHAS is sized per "
                            "active committer because that is how it bills. GHE is Azure DevOps "
                            "seats available to migrate. These are volumes, not revenue \u2014 "
                            "deliberately, since price per account is not yet negotiated.")
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
        ("Copilot seats", num(quantities["Copilot"]), "seats with no Copilot today",
         PLAY_COLOR["Innovate"]),
        ("GHAS committers", num(quantities["GHAS"]), "active committers not covered",
         PLAY_COLOR["Trust"]),
        ("GHE seats", num(quantities["GHE"]), "Azure DevOps seats to migrate", PLAY_COLOR["Scale"]),
        ("AI credits / yr", num(aiu.get("currentAnnualisedCredits")),
         "%s invoiced run-rate" % money(aiu.get("currentAnnualisedSpend")), ACCENT),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, BODY_TOP, Inches(2.95), Inches(1.42), label, value, sub, color)
        x += Inches(3.11)

    rows = [
        ["Copilot", "Bucket 2", "Seats with no Copilot today", num(quantities["Copilot"]),
         "seats"],
        ["GHAS", "Bucket 1", "Active committers L90d not covered", num(quantities["GHAS"]),
         "committers"],
        ["GHE", "Bucket 1", "Azure DevOps seats available to migrate", num(quantities["GHE"]),
         "seats"],
        ["AI credits", "Bucket 2", "Accounts consuming credits today",
         num(aiu.get("accountsConsumingAiu")),
         money(aiu.get("currentAnnualisedSpend")) + " run-rate"],
    ]
    colors = {0: PLAY_COLOR["Innovate"], 1: PLAY_COLOR["Trust"],
              2: PLAY_COLOR["Scale"], 3: ACCENT}
    deck.table(slide, MARGIN, Inches(3.42), W - 2 * MARGIN,
               ["Product", "Bucket", "Sizing basis", "Quantity", "Unit"],
               [1.6, 1.3, 6.2, 1.6, 1.8], rows, row_h=0.46, size=11.5, colors=colors)

    deck.text(slide, MARGIN, Inches(5.66), W - 2 * MARGIN, Inches(0.62),
              "This is the addressable volume in the focus set, counted in units we can verify "
              "\u2014 seats, committers and invoiced credits. What the half needs against it is "
              "on the next slide, in dated pipeline.", size=12.5, color=TEXT)
    deck.footnote(slide, "Quantities are measured, not modelled: seats and committers come from "
                         "product telemetry, credits from invoiced run-rate. No ARR is imputed.")
    return slide


def slide_7_coverage(deck, coverage, focus):
    products = {p.get("product"): p for p in coverage.get("products", []) or []}
    pipeline = coverage.get("pipeline", {})
    buckets = {b.get("bucket"): b for b in coverage.get("buckets", []) or []}
    ghe = products.get("GHE") or {}
    ghas = products.get("GHAS") or {}
    ghe_pipe = ghe.get("pipelineCoverage")
    ghas_pipe = ghas.get("pipelineCoverage")
    b1 = buckets.get("Bucket 1") or {}
    uncovered = b1.get("uncoveredGap")
    # uncoveredGap goes negative once pipeline exceeds the remaining gap. Rendering a
    # negative as "$-16K uncovered" reads as a hole when it is in fact a surplus, so
    # the sign is resolved into language here and never printed raw.
    over_covered = uncovered is not None and uncovered <= 0
    surplus = abs(uncovered) if uncovered is not None else None
    ghe_short = max(0.0, float(ghe.get("h1Target") or 0)
                    - float(ghe.get("livePipeline") or 0))

    # Every column below is a dated, invoiceable number. Nothing modelled.
    if ghe_pipe is None or ghas_pipe is None:
        narrative = ("Targets are not yet set for every product, so coverage reads TBD. Fill in "
                     "targets.json and re-run to see the uncovered gap per product.")
        note = ("Every column here is dated pipeline against a set target - no modelled "
                "potential. Coverage reads TBD wherever targets.json is not yet filled in.")
    else:
        if over_covered:
            narrative = ("Bucket 1 clears on dated pipeline - %s more than the remaining gap - "
                         "but only because GHAS runs at %.2fx. GHE is at %.2fx and still %s "
                         "short on its own line, so the half depends on GHAS landing and on "
                         "new GHE supply arriving behind it."
                         % (money(surplus), ghas_pipe, ghe_pipe, money(ghe_short)))
            note = ("Bucket 1 nets to covered, carried by GHAS at %.2fx. Read that as "
                    "concentration risk, not comfort: GHE alone is %s short at %.2fx, so if "
                    "GHAS slips there is nothing behind it. Protect the GHAS closes and keep "
                    "adding GHE migration supply."
                    % (ghas_pipe, money(ghe_short), ghe_pipe))
        else:
            narrative = ("GHAS is covered %.2fx by dated pipeline, so the H1 GHAS number is a "
                         "close-and-land problem, not a hunting problem. GHE is at %.2fx and is "
                         "the whole constraint: %s of Bucket 1 is still uncovered, and it has to "
                         "come from migration supply and new logos."
                         % (ghas_pipe, ghe_pipe,
                            money(uncovered) if uncovered is not None else "the balance"))
            note = ("GHAS at %.2fx is already covered by "
                    "dated deals, so protect it and close it. GHE at %.2fx is where the half is "
                    "won or lost - %s uncovered in Bucket 1. If asked what changes the number, "
                    "the answer is GHE migration supply, not more GHAS activity."
                    % (ghas_pipe, ghe_pipe,
                       money(uncovered) if uncovered is not None else "the balance"))

    slide = deck.slide("Coverage: target vs live, dated pipeline",
                       "Q3 \u00b7 Coverage math", note=note)
    rows, colors = [], {}

    for index, product in enumerate(coverage.get("products", []) or []):
        known = product.get("targetKnown")
        pipe_ratio = product.get("pipelineCoverage")
        rows.append([
            product.get("product", ""),
            product.get("bucket", ""),
            money(product.get("h1Target")) if known else "TBD",
            money(product.get("livePipeline")),
            ("%.2fx" % pipe_ratio) if pipe_ratio is not None else "\u2014",
            (money(max(0.0, float(product.get("h1Target") or 0)
                       - float(product.get("livePipeline") or 0)))
             if (float(product.get("h1Target") or 0)
                 - float(product.get("livePipeline") or 0)) > 0 else "Covered")
            if known else "\u2014",
        ])
        # Colour on dated pipeline: that is the number that carries risk.
        colors[index] = ratio_color(pipe_ratio)

    deck.table(slide, MARGIN, BODY_TOP, W - 2 * MARGIN,
               ["Product", "Bucket", "H1 target", "Live H1 pipeline", "Pipeline cover",
                "Uncovered"],
               [1.8, 1.8, 1.9, 2.2, 1.8, 2.6], rows, row_h=0.46, size=11.5,
               colors=colors)

    top = float(BODY_TOP) + Inches(0.3) + Inches(0.46) * len(rows) + Inches(0.32)

    by_bucket = pipeline.get("byBucket", {}) or {}
    seller = pipeline.get("seller") or 0
    cards = [
        ("Bucket 1 net-new", money(by_bucket.get("Bucket 1")),
         "GHE + GHAS, close-dated in H1", ACCENT),
        ("Bucket 2 net-new", money(by_bucket.get("Bucket 2")),
         "consumption, does not cover Bucket 1", ACCENT),
        ("Bucket 1 uncovered",
         "TBD" if uncovered is None else ("Covered" if over_covered else money(uncovered)),
         ("%s clear of the gap" % money(surplus)) if over_covered
         else "after attainment and pipeline",
         PLAY_COLOR["Scale"] if over_covered else WARN),
        ("H1 renewal pipeline", money(pipeline.get("renewal")),
         "excluded from attainment", MUTED),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, Emu(int(top)), Inches(2.94), Inches(1.3), label, value, sub, color)
        x += Inches(3.105)

    deck.text(slide, MARGIN, Emu(int(top + Inches(1.52))), W - 2 * MARGIN, Inches(0.68),
              narrative, size=12, color=TEXT)

    # Provenance. Leadership will look these numbers up in Salesforce; anything that
    # will not be found there has to be declared on the slide, not in a backup pack.
    marks = ["Targets are net-new. Renewal pipeline is shown for context only and does not "
             "count towards attainment."]
    if seller:
        # Name the accounts from the data. Hardcoding them here meant every seller who
        # ran the skill printed one particular customer's name on their own deck.
        named = sorted({a.get("name", "") for a in focus.get("accounts", [])
                        for o in (a.get("openPipeline") or [])
                        if o.get("source") == "seller" and o.get("inH1")
                        and not o.get("isRenewal") and a.get("name")})
        marks.append("Includes %s of seller-confirmed pipeline not yet raised in Salesforce%s."
                     % (money(seller),
                        (" (%s)" % ", ".join(named[:3])) if named else ""))
    inferred = pipeline.get("inferredProduct") or 0
    if inferred:
        marks.append("%s of pipeline has its product inferred from seat-based opportunity "
                     "naming rather than an explicit product field." % money(inferred))
    deck.footnote(slide, " ".join(marks))
    return slide


def slide_8_how(deck, focus, report):
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
        rows = sorted(by_play[play], key=lambda r: int(r.get("rank") or 999))
        color = PLAY_COLOR[play]
        q1 = [r for r in rows if (r.get("tier") or "").startswith(("Tier 1", "Tier 2"))][:4]
        q2 = [r for r in rows if r not in q1][:3]

        deck.fill(slide, x, BODY_TOP, col_w, Inches(4.62), PANEL, line=LINE, radius=True)
        deck.fill(slide, x, BODY_TOP, col_w, Inches(0.06), color)
        deck.text(slide, Emu(int(x + Inches(0.24))), Emu(int(BODY_TOP + Inches(0.24))),
                  Emu(int(col_w - Inches(0.48))), Inches(0.3),
                  "%s \u00b7 %d accounts" % (play.upper(), len(rows)),
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
                          Inches(0.92), Inches(0.26), "#%d" % int(account.get("rank") or 0),
                          size=10, color=color, bold=True, align=PP_ALIGN.RIGHT)
                cursor += Inches(0.26)
            cursor += Inches(0.12)
        x += Inches(4.18)

    deck.footnote(slide, "Motions are drawn from the GitHub Product Adoption Framework key "
                         "actions for each play. Account sequencing follows the composite rank.")
    return slide


def slide_9_msft_partners(deck, focus, partners, cosell=None):
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
        ("Pipeline under co-sell", money(sum(float(a.get("h1PipelineValue") or 0)
                                              for a in overlap)),
         "dated H1 deals with a TPID", WHITE),
        ("Accounts with a named partner", num(len(with_partner)),
         "existing partner relationship", PLAY_COLOR["Scale"]),
        ("Partner-led delivery need", num(len([a for a in overlap if a.get("play") == "Scale"])),
         "Scale accounts needing migration", PLAY_COLOR["Trust"]),
    ]
    x = MARGIN
    for label, value, sub, color in cards:
        deck.card(slide, x, BODY_TOP, Inches(2.95), Inches(1.42), label, value, sub, color)
        x += Inches(3.11)

    # The table body holds 7 rows before it runs into the caption below, so the
    # co-sell watchlist takes its slots from the ranked list rather than extending
    # past the plate.
    focus_ids = {a.get("salesforceId") for a in accounts}
    watchlist = [a for a in (cosell or []) if a.get("salesforceId") not in focus_ids][:2]
    top_overlap = sorted(overlap, key=lambda a: int(a.get("rank") or 999))[:7 - len(watchlist)]
    rows, colors = [], {}
    for index, account in enumerate(top_overlap):
        entry = partner_map.get(account.get("salesforceId"), {}) or {}
        names = [p.get("name") for p in (entry.get("partners") or [])
                 if p.get("name") and p.get("name") != "Invalid"]
        rows.append([
            truncate(account.get("name", ""), 26),
            account.get("play", ""),
            "#%d" % int(account.get("rank") or 0),
            (account.get("tpids") or [""])[0],
            truncate(", ".join(names) if names else "No partner mapped \u2014 needs sourcing", 46),
        ])
        colors[index] = PLAY_COLOR.get(account.get("play"), ACCENT)

    # Accounts I am working with the Microsoft team that carry no product footprint
    # yet. They have no rank because there is nothing in the data to rank them on -
    # showing them with a blank rank is the honest rendering, not an omission.
    for account in watchlist:
        index = len(rows)
        rows.append([
            truncate(account.get("name", ""), 26),
            account.get("play", ""),
            "\u2014",
            (account.get("tpids") or [""])[0] or "Seller-asserted",
            "Prospect \u2014 no footprint yet; Microsoft-led",
        ])
        colors[index] = MUTED

    deck.table(slide, MARGIN, Inches(3.42), W - 2 * MARGIN,
               ["Account", "Play", "Rank", "Microsoft TPID", "Partner"],
               [3.0, 1.5, 1.0, 2.2, 4.4], rows, row_h=0.36, size=10.5, colors=colors)

    deck.text(slide, MARGIN, Inches(6.4), W - 2 * MARGIN, Inches(0.42),
              "How I use it: TPID accounts get a joint account-team introduction before any "
              "GitHub-only outreach; Scale accounts get a partner attached to the migration "
              "before the technical win, so delivery is never the reason a deal slips.",
              size=11.5, color=MUTED)
    deck.footnote(slide, "TPIDs from Salesforce MSFT_All_TPIDs__c / MS_Sales_TPID_Best_Match__c. "
                         "Partner relationships from Salesforce Partner records.")
    return slide


def slide_10_working(deck, learnings):
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


def slide_11_asks(deck, coverage, focus, learnings):
    slide = deck.slide("Asks", "Q7 \u00b7 Leadership and cross-functional",
                       note="Each ask is tied to a specific number on an earlier slide, so it is "
                            "answerable rather than aspirational.")
    facts = learnings.get("facts", {})
    products = {p.get("product"): p for p in coverage.get("products", []) or []}
    ghe = products.get("GHE", {})
    ghas = products.get("GHAS", {})

    leadership = []
    if ghe.get("targetKnown"):
        b1 = next((b for b in coverage.get("buckets", []) or []
                   if b.get("bucket") == "Bucket 1"), {})
        gap = b1.get("uncoveredGap")
        ghe_short = max(0.0, float(ghe.get("h1Target") or 0)
                        - float(ghe.get("livePipeline") or 0))
        if gap is not None and gap <= 0:
            # Bucket 1 nets out only because GHAS over-covers. The ask is still real,
            # so it is framed on the GHE line rather than the netted bucket.
            leadership.append(
                "GHE supply: %s is close-dated against a %s H1 target (%.2fx), %s short on "
                "the GHE line. Bucket 1 only nets to covered because GHAS is carrying it, so "
                "I need migration-led demand generation or account additions on GHE rather "
                "than relying on that concentration holding."
                % (money(ghe.get("livePipeline")), money(ghe.get("h1Target")),
                   ghe.get("pipelineCoverage") or 0, money(ghe_short)))
        else:
            leadership.append(
                "GHE supply: %s is close-dated against a %s H1 target (%.2fx), leaving %s of "
                "Bucket 1 uncovered. I need migration-led demand generation or account "
                "additions to close the supply gap, not just conversion pressure."
                % (money(ghe.get("livePipeline")), money(ghe.get("h1Target")),
                   ghe.get("pipelineCoverage") or 0,
                   money(gap) if gap is not None else "the balance"))
    else:
        leadership.append(
            "GHE target: not yet set. I have %s of dated GHE pipeline in the focus set - I "
            "need the target so I can tell you whether that is coverage or a supply gap."
            % money(ghe.get("livePipeline")))

    consumption = products.get("Consumption") or {}
    if not consumption.get("targetKnown"):
        leadership.append(
            "Bucket 2 target: consumption target is still unset. I am carrying %s of dated "
            "consumption pipeline and %s attained - I need the number to plan against."
            % (money(consumption.get("livePipeline")),
               money(bucket_of(coverage, "Bucket 2").get("attainedH1"))))

    ghas_pipe = ghas.get("pipelineCoverage")
    if ghas_pipe is not None and ghas_pipe >= 1:
        leadership.append(
            "GHAS delivery capacity: GHAS is already %.2fx covered by dated pipeline (%s). "
            "The risk is no longer sourcing it, it is landing it \u2014 I need "
            "security-specialist time to get these to production, not more pipeline."
            % (ghas_pipe, money(ghas.get("livePipeline"))))
    else:
        leadership.append(
            "GHAS technical capacity: %d of %d focus accounts consume GHAS today, against %s "
            "of dated GHAS pipeline. Converting that needs security-specialist time, not more "
            "pipeline." % (facts.get("consumingAccounts", {}).get("ghas", 0),
                           facts.get("focusCount", 0), money(ghas.get("livePipeline"))))

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
    b1_pipe = (coverage.get("pipeline", {}) or {}).get("byBucket", {}).get("Bucket 1")
    commitment = (
        "Commitment: %s of Bucket 1 gap closed across H1, worked through %d focus accounts "
        "with %s already in dated pipeline." % (money(b1_gap), focus.get("selectedCount", 0),
                                                money(b1_pipe))
        if b1_gap else
        "Commitment: %d focus accounts with %s in dated pipeline, worked to the plan on the "
        "previous slides." % (focus.get("selectedCount", 0), money(b1_pipe))
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

    # Seller-asserted co-sell accounts: named on the Microsoft slide even though they
    # carry no product signal and therefore cannot earn a rank. The play comes from
    # the report, the co-sell flag from the CRM context, so join them here.
    crm = load(run_dir, "crm-context.json", {}) or {}
    plays_by_id = {a.get("salesforceId"): a.get("primaryPlay")
                   for a in (report or {}).get("accounts", []) or []}
    cosell = [{"salesforceId": sid, "name": rec.get("name", ""),
               "tpids": rec.get("tpids") or [],
               "play": plays_by_id.get(sid, "")}
              for sid, rec in ((crm.get("accounts") or {}).items())
              if rec.get("msftCoSell")]
    cosell.sort(key=lambda a: a["name"].lower())

    deck = Deck()
    slide_1_scorecard(deck, coverage, focus)
    slide_2_learnings(deck, learnings)
    slide_3_key_deals(deck, focus, crm, report)
    slide_4_key_accounts(deck, focus)
    slide_5_portfolio(deck, focus, coverage)
    slide_6_the_number(deck, potential, focus, coverage)
    slide_7_coverage(deck, coverage, focus)
    slide_8_how(deck, focus, report)
    slide_9_msft_partners(deck, focus, partners, cosell)
    slide_10_working(deck, learnings)
    slide_11_asks(deck, coverage, focus, learnings)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    deck.save(out_path)
    print(json.dumps({"deckPath": out_path, "slides": len(deck.prs.slides._sldIdLst)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
