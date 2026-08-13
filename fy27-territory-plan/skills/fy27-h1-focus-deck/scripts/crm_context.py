"""Bridge Salesforce CRM context (Microsoft TPID overlap + open pipeline) into the plan.

    python3 crm_context.py query <report.json> [runDir]
    python3 crm_context.py ingest <raw.json> <runDir> [--as-of YYYY-MM-DD]

Two modes, matching the actuals.py contract, because this agent cannot reach
Salesforce directly: `query` prints the SOQL to run through the Revenue MCP
`query_salesforce` tool, and `ingest` folds whatever came back into
`crm-context.json` for rank.py and exec_deck.py to consume.

`raw.json` is {"accounts": <tool output>, "opportunities": <tool output>} where
each value is whatever `query_salesforce` returned — the row extraction is
tolerant of the usual envelopes.

Output shape:
    {"accounts": {"<salesforceId>": {
        "tpids": ["54839153"],
        "msftOverlap": true,
        "openPipeline": [{"name","stage","amount","closeDate","type","forecast","stale","inH1"}],
        "h1PipelineValue": 46381.0,      # non-renewal, dated inside H1, only
        "h1RenewalValue": 0.0,
        "stalePipelineValue": 0.0,
        "bestStage": "Determined Need"}},
     "coverage": {...}, "window": {...}}

Renewals are tracked but held apart from `h1PipelineValue`: the targets this plan
is measured against are net-new/expansion, so counting a renewal towards them
would overstate coverage.
"""
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from actuals import num, pick, rows_of  # noqa: E402  (shared envelope handling)

CHUNK = 200

# GitHub's fiscal year mirrors Microsoft's: FY27 H1 = Jul-Dec 2026. Deriving the
# window from a date rather than hardcoding it keeps the script usable next half.
def fiscal_h1(as_of):
    """(fyLabel, h1Start, h1End, q1End) for the fiscal half that `as_of` sits in."""
    fy = as_of.year + 1 if as_of.month >= 7 else as_of.year
    start_year = fy - 1
    if as_of.month >= 7:
        h1 = (date(start_year, 7, 1), date(start_year, 12, 31), date(start_year, 9, 30))
    else:
        # Jan-Jun is H2; the "current" half for planning purposes is still the next H1.
        h1 = (date(fy, 7, 1), date(fy, 12, 31), date(fy, 9, 30))
    return "FY%d" % (fy % 100), h1[0], h1[1], h1[2]


ACCOUNT_QUERY = """SELECT Id, Name, MSFT_TPID__c, MSFT_All_TPIDs__c, MS_Sales_TPID_Best_Match__c
FROM Account WHERE Id IN (%s)"""

OPPORTUNITY_QUERY = """SELECT Id, Name, AccountId, StageName, Amount, CloseDate, Type,
ForecastCategoryName, NextStep
FROM Opportunity WHERE IsClosed = false AND AccountId IN (%s)
ORDER BY Amount DESC NULLS LAST"""

RENEWAL_TYPES = {"renewal"}

# Stages late enough that the deal is a credible half-commit rather than an aspiration.
# Used only to rank, never to inflate value.
ADVANCED_STAGES = {
    "verbal agreement": 1.0,
    "proposal & negotiation": 0.9,
    "business selected": 0.8,
    "determined need": 0.6,
    "manage & optimize": 0.5,
    "qualified": 0.4,
    "problem identification": 0.3,
}


def account_ids(report):
    seen, ids = set(), []
    for acct in report.get("accounts", []):
        sid = (acct.get("salesforceId") or "").strip()
        if sid and sid not in seen:
            seen.add(sid)
            ids.append(sid)
    return ids


def emit_queries(report):
    ids = account_ids(report)
    out = []
    for i in range(0, len(ids), CHUNK):
        lit = ",".join("'%s'" % s for s in ids[i:i + CHUNK])
        out.append(("accounts", ACCOUNT_QUERY % lit))
        out.append(("opportunities", OPPORTUNITY_QUERY % lit))
    return ids, out


def split_tpids(*values):
    """MSFT_All_TPIDs__c is a comma-joined string; the others are single ids."""
    found = []
    for value in values:
        if not value:
            continue
        for part in re.split(r"[,;\s]+", str(value)):
            part = part.strip()
            if part and part.isdigit() and part not in found:
                found.append(part)
    return found


def stage_weight(stage):
    return ADVANCED_STAGES.get(str(stage or "").strip().lower(), 0.3)


def ingest(raw, as_of):
    _, h1_start, h1_end, _ = fiscal_h1(as_of)
    accounts = {}

    for row in rows_of(raw.get("accounts")):
        sid = pick(row, "Id", "id")
        if not sid:
            continue
        tpids = split_tpids(
            pick(row, "MSFT_TPID__c"),
            pick(row, "MSFT_All_TPIDs__c"),
            pick(row, "MS_Sales_TPID_Best_Match__c"),
        )
        accounts[str(sid)] = {
            "name": pick(row, "Name", "name") or "",
            "tpids": tpids,
            "msftOverlap": bool(tpids),
            "openPipeline": [],
            "h1PipelineValue": 0.0,
            "h1RenewalValue": 0.0,
            "stalePipelineValue": 0.0,
            "bestStage": "",
            "bestStageWeight": 0.0,
        }

    stale_count = 0
    for row in rows_of(raw.get("opportunities")):
        sid = pick(row, "AccountId", "accountId")
        if not sid:
            continue
        rec = accounts.setdefault(str(sid), {
            "name": "", "tpids": [], "msftOverlap": False, "openPipeline": [],
            "h1PipelineValue": 0.0, "h1RenewalValue": 0.0, "stalePipelineValue": 0.0,
            "bestStage": "", "bestStageWeight": 0.0,
        })
        close = str(pick(row, "CloseDate", "closeDate") or "")[:10]
        amount = num(pick(row, "Amount", "amount"))
        otype = str(pick(row, "Type", "type") or "").strip()
        stage = str(pick(row, "StageName", "stageName") or "").strip()
        # A close date in the past means the record is not a forecastable deal, whatever
        # its stage says. It is surfaced as hygiene, never scored as live.
        stale = bool(close) and close < as_of.isoformat()
        in_h1 = bool(close) and h1_start.isoformat() <= close <= h1_end.isoformat()
        is_renewal = otype.lower() in RENEWAL_TYPES

        rec["openPipeline"].append({
            "name": pick(row, "Name", "name") or "",
            "stage": stage,
            "amount": amount,
            "closeDate": close,
            "type": otype,
            "forecast": pick(row, "ForecastCategoryName") or "",
            "stale": stale,
            "inH1": in_h1,
            "isRenewal": is_renewal,
        })
        if stale:
            rec["stalePipelineValue"] += amount
            stale_count += 1
            continue
        if in_h1:
            if is_renewal:
                rec["h1RenewalValue"] += amount
            else:
                rec["h1PipelineValue"] += amount
                weight = stage_weight(stage)
                if weight > rec["bestStageWeight"]:
                    rec["bestStageWeight"] = weight
                    rec["bestStage"] = stage

    for rec in accounts.values():
        rec["openPipeline"].sort(key=lambda o: -o["amount"])

    with_tpid = sum(1 for r in accounts.values() if r["msftOverlap"])
    with_pipe = sum(1 for r in accounts.values() if r["h1PipelineValue"] > 0)
    return {
        "accounts": accounts,
        "window": {"h1Start": h1_start.isoformat(), "h1End": h1_end.isoformat(),
                   "asOf": as_of.isoformat()},
        "coverage": {
            "accounts": len(accounts),
            "accountsWithTpid": with_tpid,
            "accountsWithH1Pipeline": with_pipe,
            "h1PipelineValue": round(sum(r["h1PipelineValue"] for r in accounts.values()), 2),
            "h1RenewalValue": round(sum(r["h1RenewalValue"] for r in accounts.values()), 2),
            "stalePipelineValue": round(sum(r["stalePipelineValue"] for r in accounts.values()), 2),
            "staleOpportunities": stale_count,
        },
    }


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    mode = sys.argv[1]

    if mode == "query":
        with open(sys.argv[2], "r", encoding="utf-8") as fh:
            report = json.load(fh)
        run_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(sys.argv[2])
        ids, queries = emit_queries(report)
        out = os.path.join(run_dir, "crm-queries.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([{"kind": k, "soql": q} for k, q in queries], fh, indent=1)
        print(json.dumps({"queryPath": out, "accounts": len(ids),
                          "queries": len(queries)}))
        for kind, soql in queries:
            print("\n--- %s ---\n%s" % (kind, soql))
        return

    if mode == "ingest":
        with open(sys.argv[2], "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        run_dir = sys.argv[3]
        as_of = date.today()
        if "--as-of" in sys.argv:
            as_of = date.fromisoformat(sys.argv[sys.argv.index("--as-of") + 1])
        result = ingest(raw, as_of)
        out = os.path.join(run_dir, "crm-context.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1)
        summary = {"crmContextPath": out}
        summary.update(result["coverage"])
        print(json.dumps(summary))
        return

    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
