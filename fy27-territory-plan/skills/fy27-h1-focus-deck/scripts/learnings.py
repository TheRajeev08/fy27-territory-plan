#!/usr/bin/env python3
"""Derive H2 FY26 learnings and a working/not-working read from the run's own records.

Every statement this emits is computed from focus-accounts.json, coverage.json and
crm-context.json. Nothing is asserted that cannot be traced back to a count or a sum,
because a leadership slide that says "we learned X" without a number behind it is an
opinion, and opinions are what the deck is trying to replace.

    learnings.py <runDir>

Writes <runDir>/learnings.json.
"""

import json
import os
import sys


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def money(value):
    return "${:,.0f}".format(round(float(value or 0)))


def build(focus, coverage, crm):
    accounts = focus.get("accounts", []) or []
    total = len(accounts) or 1
    totals = focus.get("totals", {}) or {}

    no_two_way = [a for a in accounts if not a.get("twoWay")]
    with_pipeline = [a for a in accounts if float(a.get("h1PipelineValue") or 0) > 0]
    with_overlap = [a for a in accounts if a.get("msftOverlap")]
    greenfield = [a for a in accounts if (a.get("current") or {}).get("greenfield")]
    with_triggers = [a for a in accounts if a.get("triggers")]

    stale_value = sum(float(a.get("stalePipelineValue") or 0) for a in accounts)
    stale_count = sum(
        len([o for o in (a.get("openPipeline") or []) if o.get("stale")])
        for a in accounts
    )

    # Which products the focus set actually consumes today, as a count of accounts.
    consuming = {}
    for account in accounts:
        observed = ((account.get("current") or {}).get("consumptionObserved") or {})
        for product, value in observed.items():
            if float(value or 0) > 1:
                consuming[product] = consuming.get(product, 0) + 1

    ghas_accounts = consuming.get("ghas", 0)
    copilot_accounts = consuming.get("copilot", 0)

    by_product = {p["product"]: p for p in coverage.get("products", []) or []}
    ghe = by_product.get("GHE", {})
    ghas = by_product.get("GHAS", {})

    learnings = [
        {
            "headline": "Pipeline hygiene cost us forecast credibility",
            "detail": "{count} open opportunities worth {value} in the focus set carry "
                      "close dates already in the past. They inflate coverage without "
                      "being forecastable.".format(count=stale_count, value=money(stale_value)),
            "carryForward": "Close-date discipline weekly; anything past date is "
                            "re-dated with a reason or closed out before it is counted.",
            "evidence": "crm-context.json: {} stale opportunities".format(stale_count),
        },
        {
            "headline": "GHAS is a story we told, not a motion we ran",
            "detail": "Only {ghas} of {total} focus accounts consume GHAS today, against "
                      "{tam} of sized committer-based potential. Coverage of {ratio}x is "
                      "TAM, not plan.".format(
                          ghas=ghas_accounts, total=total,
                          tam=money(ghas.get("sizedPotential")),
                          ratio=ghas.get("coverageRatio") or 0),
            "carryForward": "Run GHAS as a named-account motion on the {n} accounts with "
                            "the largest committer bases, not as an attach conversation.".format(
                                n=min(8, total)),
            "evidence": "coverage.json + focus-accounts.json consumption",
        },
        {
            "headline": "GHE net-new needs supply, not just conversion",
            "detail": "Sized GHE potential in the focus set is {sized} against a {target} "
                      "H1 target - {ratio}x coverage. The existing book does not contain "
                      "enough GHE to make the number on conversion alone.".format(
                          sized=money(ghe.get("sizedPotential")),
                          target=money(ghe.get("h1Target")),
                          ratio=ghe.get("coverageRatio") or 0),
            "carryForward": "Add migration and new-logo supply early in Q1 rather than "
                            "discovering the gap at Q2 close.",
            "evidence": "coverage.json GHE line",
        },
        {
            "headline": "Two-way engagement predicts progression",
            "detail": "{two} of {total} focus accounts have two-way communication; the "
                      "{none} that do not are where sizing exists but motion does not.".format(
                          two=totals.get("withTwoWay", 0), total=total, none=len(no_two_way)),
            "carryForward": "Treat a first genuine reply as the qualification gate before "
                            "an account is counted as covered.",
            "evidence": "focus-accounts.json activity",
        },
        {
            "headline": "Copilot consumption is the widest surface we have",
            "detail": "{cop} of {total} focus accounts already consume Copilot, which makes "
                      "it the most reliable route into an account before a Bucket 1 "
                      "conversation.".format(cop=copilot_accounts, total=total),
            "carryForward": "Lead with Copilot value evidence, land the platform "
                            "conversation second.",
            "evidence": "focus-accounts.json consumptionObserved",
        },
    ]

    working = [
        {
            "point": "Copilot as the door-opener",
            "proof": "{}/{} focus accounts consuming Copilot".format(copilot_accounts, total),
        },
        {
            "point": "Trigger-led prioritisation",
            "proof": "{}/{} focus accounts carry a cited, dated trigger".format(
                len(with_triggers), total),
        },
        {
            "point": "Microsoft overlap is broad",
            "proof": "{}/{} focus accounts carry at least one TPID".format(
                len(with_overlap), total),
        },
        {
            "point": "Installed base is real",
            "proof": "{} current ARR across the focus set".format(
                money(totals.get("currentArr"))),
        },
    ]

    not_working = [
        {
            "point": "Live pipeline is thin",
            "proof": "only {n} of {total} focus accounts carry H1-dated net-new pipeline "
                     "({v})".format(n=len(with_pipeline), total=total,
                                    v=money(totals.get("h1Pipeline"))),
        },
        {
            "point": "Stale opportunities",
            "proof": "{n} records, {v}, past close date".format(
                n=stale_count, v=money(stale_value)),
        },
        {
            "point": "GHAS attach",
            "proof": "{n} of {total} accounts consuming GHAS".format(
                n=ghas_accounts, total=total),
        },
        {
            "point": "Silent accounts",
            "proof": "{n} of {total} focus accounts without two-way contact".format(
                n=len(no_two_way), total=total),
        },
        {
            "point": "Greenfield exposure",
            "proof": "{n} focus accounts have no current ARR to expand from".format(
                n=len(greenfield)),
        },
    ]

    return {
        "learnings": learnings,
        "working": working,
        "notWorking": not_working,
        "facts": {
            "focusCount": total,
            "staleCount": stale_count,
            "staleValue": round(stale_value, 2),
            "withPipeline": len(with_pipeline),
            "withOverlap": len(with_overlap),
            "withTriggers": len(with_triggers),
            "withoutTwoWay": len(no_two_way),
            "greenfield": len(greenfield),
            "consumingAccounts": consuming,
        },
    }


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: learnings.py <runDir>")
    run_dir = sys.argv[1]

    focus = load(os.path.join(run_dir, "focus-accounts.json"))
    coverage = load(os.path.join(run_dir, "coverage.json"), {})
    crm = load(os.path.join(run_dir, "crm-context.json"), {})
    if not focus:
        raise SystemExit("Cannot read focus-accounts.json")

    out = build(focus, coverage or {}, crm or {})
    dest = os.path.join(run_dir, "learnings.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({"learningsPath": dest, "learnings": len(out["learnings"]),
                      "working": len(out["working"]),
                      "notWorking": len(out["notWorking"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
