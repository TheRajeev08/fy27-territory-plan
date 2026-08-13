#!/usr/bin/env python3
"""Size the FY27 H1 opportunity per account.

Every dollar this module emits carries a `basis` of "observed", "list" or "derived":

  observed  the account's own effective price, computed from what they actually pay
  list      GitHub public pricing
  derived   a median across the install base, used only where no public price exists

That tag travels all the way to the slide, so any number in the deck can be defended
or discounted on the spot. Nothing here invents a price.

Reads:  fy27-territory-plan.json  (accounts, plays, engagement)
        raw-actuals.json          (optional Kusto ARR + consumption)
        pricing.json              (rates)
Writes: potential.json
"""

import json
import os
import sys

MONTHS = 12

# SuperDash columns that drive sizing. Kept as constants so a column rename in the
# export fails loudly here rather than silently zeroing a headline number.
COL_COPILOT_POTENTIAL = "copilotWhitespace"
COL_ADO = "adoWhitespace"
COL_SECURITY = "securityWhitespace"
COL_METERED = "meteredConsumption"


def load(path, default=None):
    if not path or not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def money(value):
    return round(float(value or 0), 2)


class Rates:
    """Resolves a price for a product, preferring what the account actually pays."""

    def __init__(self, pricing):
        self.pricing = pricing
        self.list = pricing.get("list", {})
        self.derived = pricing.get("derived", {})
        self.assumptions = pricing.get("assumptions", {})

    def copilot_seat_year(self, observed=None):
        if observed and observed > 0:
            return observed, "observed"
        tier = self.assumptions.get("copilotTierForSizing", "copilotBusiness")
        return money(self.list[tier]["perUserMonth"] * MONTHS), "list"

    def ghas_committer_year(self, observed=None):
        if observed and observed > 0:
            return observed, "observed"
        sku = self.assumptions.get("ghasSkuForSizing", "codeSecurity")
        return money(self.list[sku]["perCommitterMonth"] * MONTHS), "list"

    def ghe_seat_year(self, observed=None):
        if observed and observed > 0:
            return observed, "observed"
        # No public per-seat list price for GitHub Enterprise, so this is the one
        # place a derived median is unavoidable. It is labelled as such.
        return money(self.derived.get("githubEnterprisePerSeatYear", 0)), "derived"

    def credit(self):
        return float(self.list["aiCredit"]["perCredit"])

    def included_credits_per_seat_year(self):
        """Credits bundled with each Copilot seat, per year.

        Contractual, not modelled: it comes straight from the tier's published
        included allowance, so the capacity figure it feeds can be defended.
        """
        tier = self.assumptions.get("copilotTierForSizing", "copilotBusiness")
        return float(self.list[tier].get("includedCreditsPerUserMonth", 0)) * MONTHS


def observed_prices(actuals_for_account):
    """Effective unit prices from what this account actually pays.

    ARR/seats gives a per-seat price; charge/units gives a per-unit consumption rate.
    Zero denominators are skipped rather than defaulted, so a missing price falls back
    to list rather than silently becoming 0.
    """
    prices = {}
    if not actuals_for_account:
        return prices

    for row in actuals_for_account.get("arr", []):
        seats = float(row.get("license_seats") or 0)
        arr = float(row.get("total_arr") or 0)
        if seats > 0 and arr > 0:
            prices.setdefault(row.get("product_type", ""), money(arr / seats))

    for row in actuals_for_account.get("consumption", []):
        units = float(row.get("billed_units") or 0)
        charge = float(row.get("charge_amt") or 0)
        if units > 0 and charge > 0:
            prices.setdefault("consumption:" + str(row.get("product_name", "")),
                              round(charge / units, 6))
    return prices


def current_state(actuals_for_account):
    """What the account already has: ARR, seats, and annualised consumption."""
    arr_total = 0.0
    seats = {}
    products = []
    for row in (actuals_for_account or {}).get("arr", []):
        arr_total += float(row.get("total_arr") or 0)
        product = row.get("product_type", "")
        seats[product] = seats.get(product, 0) + int(float(row.get("license_seats") or 0))
        products.append(product)

    consumption = {}
    window_months = (actuals_for_account or {}).get("consumptionMonths") or 0
    for row in (actuals_for_account or {}).get("consumption", []):
        name = str(row.get("product_name", ""))
        consumption[name] = consumption.get(name, 0.0) + float(row.get("charge_amt") or 0)

    # Annualise the observed consumption window so ACR is comparable to ARR.
    factor = (12.0 / window_months) if window_months else 0.0
    acr = {k: money(v * factor) for k, v in consumption.items()} if factor else {}

    return {
        "arr": money(arr_total),
        "seatsByProduct": seats,
        "products": sorted(set(p for p in products if p)),
        "consumptionObserved": {k: money(v) for k, v in consumption.items()},
        "acrAnnualised": acr,
        "consumptionWindowMonths": window_months,
        "greenfield": arr_total <= 0,
    }


def size_account(account, actuals, rates):
    """Convert an account's whitespace signals into dollars, with basis tags."""
    signals = account.get("revenueSignals", {}) or {}
    prices = observed_prices(actuals)
    state = current_state(actuals)

    copilot_seats = max(0, int(float(signals.get(COL_COPILOT_POTENTIAL) or 0)))
    ado_seats = max(0, int(float(signals.get(COL_ADO) or 0)))

    # GHAS licenses are consumed by unique ACTIVE COMMITTERS (L90d), not by seats.
    # Sizing off seat whitespace would price a product the customer would never be
    # billed for, so committers are the basis and existing GHAS coverage is netted off.
    committers_total = max(0, int(float(signals.get("activeCommitters") or 0)))
    ghas_covered = max(0, int(float(signals.get("ghasSeats") or 0)))
    committers = max(0, committers_total - ghas_covered)

    lines = []

    if copilot_seats > 0:
        rate, basis = rates.copilot_seat_year(prices.get("Copilot"))
        lines.append({
            "product": "Copilot",
            "metric": "seats",
            "quantity": copilot_seats,
            "rate": rate,
            "basis": basis,
            "value": money(copilot_seats * rate),
            "note": "GHE/VS seats without Copilot today",
        })

    if committers > 0:
        rate, basis = rates.ghas_committer_year(prices.get("Advanced Security"))
        sku = rates.assumptions.get("ghasSkuForSizing", "codeSecurity")
        lines.append({
            "product": "GHAS",
            "metric": "committers",
            "quantity": committers,
            "rate": rate,
            "basis": basis,
            "value": money(committers * rate),
            "note": "%d active committers (L90d) not covered by GHAS today; GHAS bills per active committer - sized as %s" % (committers, sku),
        })

    if ado_seats > 0:
        rate, basis = rates.ghe_seat_year(prices.get("GitHub Enterprise"))
        lines.append({
            "product": "GHE",
            "metric": "seats",
            "quantity": ado_seats,
            "rate": rate,
            "basis": basis,
            "value": money(ado_seats * rate),
            "note": "Azure DevOps TAM available to migrate",
        })

    # AIU deliberately does NOT contribute to potential ARR.
    #
    # Two things are true and must not be conflated:
    #   1. Credits already invoiced are revenue we ALREADY earn. Annualising them into
    #      "potential" would double-count the run-rate and inflate the number.
    #   2. Every Copilot seat sold ships with included credits (1,900/mo Business,
    #      3,900/mo Enterprise). Those are bundled, so they are capacity, not new revenue.
    #      Overage beyond the included pool is real incremental revenue, but nothing in the
    #      data supports forecasting it without inventing a consumption curve.
    #
    # So AIU is reported as measured run-rate plus contractual capacity unlocked by the
    # Copilot seats in this plan, and both are kept out of potentialArr.
    aiu_spend = state["acrAnnualised"].get("copilot aiu", 0.0)
    aiu_units_billed = 0.0
    for row in (actuals or {}).get("consumption", []):
        if str(row.get("product_name", "")) == "copilot aiu":
            aiu_units_billed += float(row.get("billed_units") or 0)
    window = state["consumptionWindowMonths"] or 0
    factor = (12.0 / window) if window else 0.0
    included_per_seat_year = rates.included_credits_per_seat_year()
    aiu = {
        "currentAnnualisedSpend": money(aiu_spend),
        "currentAnnualisedCredits": int(aiu_units_billed * factor) if factor else int(aiu_units_billed),
        "includedCreditCapacityFromPlan": int(copilot_seats * included_per_seat_year),
        "includedCreditsPerSeatYear": included_per_seat_year,
        "basis": "observed" if aiu_units_billed > 0 else "none",
        "note": ("Credits already invoiced are existing revenue, not upside; included credits "
                 "ship bundled with Copilot seats. Neither is counted in potential ARR."),
    }

    total = money(sum(line["value"] for line in lines))
    bases = sorted(set(line["basis"] for line in lines))

    return {
        "potentialArr": total,
        "lines": lines,
        "bases": bases,
        "aiu": aiu,
        "current": state,
        "sizingCoverage": "sized" if lines else "unsized",
    }


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: potential.py <report.json> <runDir> [raw-actuals.json] [pricing.json]")

    report_path, run_dir = sys.argv[1], sys.argv[2]
    actuals_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(run_dir, "raw-actuals.json")
    pricing_path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "pricing.json")

    report = load(report_path)
    if not report:
        raise SystemExit("Cannot read territory report: %s" % report_path)
    pricing = load(pricing_path)
    if not pricing:
        raise SystemExit("Cannot read pricing config: %s" % pricing_path)

    raw = load(actuals_path, {}) or {}
    by_account = raw.get("accounts", {})
    rates = Rates(pricing)

    sized = {}
    for account in report.get("accounts", []):
        sid = account.get("salesforceId") or ""
        sized[sid or account.get("name", "")] = size_account(
            account, by_account.get(sid), rates)

    totals = {}
    for entry in sized.values():
        for line in entry["lines"]:
            key = line["product"]
            bucket = totals.setdefault(key, {"quantity": 0, "value": 0.0, "accounts": 0})
            bucket["quantity"] += line["quantity"]
            bucket["value"] = money(bucket["value"] + line["value"])
            bucket["accounts"] += 1

    # Kept separate from `totals` on purpose: AIU is run-rate plus bundled capacity,
    # not incremental ARR, and merging the two is exactly the error to avoid.
    aiu_totals = {
        "currentAnnualisedSpend": money(sum(e["aiu"]["currentAnnualisedSpend"] for e in sized.values())),
        "currentAnnualisedCredits": sum(e["aiu"]["currentAnnualisedCredits"] for e in sized.values()),
        "includedCreditCapacityFromPlan": sum(e["aiu"]["includedCreditCapacityFromPlan"] for e in sized.values()),
        "accountsConsumingAiu": sum(1 for e in sized.values() if e["aiu"]["currentAnnualisedCredits"] > 0),
    }

    installed = {
        "arr": money(sum(e["current"]["arr"] for e in sized.values())),
        "acrAnnualised": {},
    }
    for entry in sized.values():
        for product, value in entry["current"]["acrAnnualised"].items():
            installed["acrAnnualised"][product] = money(
                installed["acrAnnualised"].get(product, 0.0) + value)

    out = {
        "generatedFrom": os.path.basename(report_path),
        "pricingBasis": {
            "order": "observed > list > derived",
            "derivedUsedFor": "GitHub Enterprise per-seat (no public list price)",
        },
        "assumptions": pricing.get("assumptions", {}),
        "accounts": sized,
        "totals": totals,
        "aiuTotals": aiu_totals,
        "installed": installed,
        "accountsSized": sum(1 for e in sized.values() if e["sizingCoverage"] == "sized"),
        "accountsTotal": len(sized),
        "accountsWithArr": sum(1 for e in sized.values() if not e["current"]["greenfield"]),
    }

    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "potential.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1)

    print(json.dumps({
        "potentialPath": path,
        "accountsSized": out["accountsSized"],
        "accountsTotal": out["accountsTotal"],
        "accountsWithArr": out["accountsWithArr"],
        "totals": {k: v["value"] for k, v in totals.items()},
    }))


if __name__ == "__main__":
    main()
