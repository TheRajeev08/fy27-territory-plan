"""Rank the book down to the H1 focus accounts.

Leadership asked for 30-50 accounts chosen on three factors: potential ARR, active
communication, and recent live triggers. Those factors are not available at the same
time - triggers cost a web search per account, so fetching them for all 251 accounts
would be slow and mostly wasted. Hence two stages:

    stage1  potential + communication            -> candidate shortlist (~60)
    stage2  potential + communication + triggers -> final selection (30-50)

Stage 1 deliberately over-selects. An account with a strong trigger but middling
potential still needs to be reachable in stage 2, so the shortlist is ~1.5x the final
count rather than exactly the final count.

Scores are normalised to 0-100 against the book, so a score answers "how does this
account compare to the rest of my territory" rather than carrying a unit of its own.

    rank.py stage1 <report.json> <potential.json> <runDir> [--candidates N]
    rank.py stage2 <report.json> <potential.json> <runDir> [--triggers f] [--count N]
"""

import json
import math
import os
import sys
from datetime import date, datetime

DEFAULT_FINAL = 40
MIN_FINAL, MAX_FINAL = 30, 50
CANDIDATE_MULTIPLIER = 1.5

# A focus account has to belong to a play: the deck organises Q2 and Q4 by play, so an
# unclassified account has nothing to be presented against no matter how it scores.
PLAYS = ("Innovate", "Trust", "Scale")

# Weights sum to 1.0. Potential leads because the ask is a revenue plan; communication
# is weighted next because a warm account is materially likelier to close in a half;
# triggers are the tiebreaker that says "why now" rather than "how big".
W_STAGE1 = {"potential": 0.65, "communication": 0.35}
# Stage 2 adds open pipeline as a fourth signal. An account carrying a live, H1-dated
# opportunity is demonstrably in-motion, which is a stronger claim than sizing alone.
W_STAGE2 = {"potential": 0.40, "pipeline": 0.20, "communication": 0.20, "trigger": 0.20}

# A trigger is worth more when it implies budget or urgency. These weights are applied
# to the trigger's type; recency then decays it.
TRIGGER_TYPE_WEIGHT = {
    "funding": 1.0,
    "acquisition": 1.0,
    "security_incident": 1.0,
    "leadership_change": 0.9,
    "ai_launch": 0.9,
    "product_launch": 0.7,
    "expansion": 0.7,
    "partnership": 0.6,
    "earnings": 0.5,
    "recognition": 0.4,
    "other": 0.3,
}
TRIGGER_HALF_LIFE_DAYS = 120.0


def load(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def normalise(values):
    """Scale to 0-100 using log compression.

    Potential ARR is heavily skewed - a handful of accounts are worth 50x the median.
    Linear scaling would push everything else to near-zero and make the composite
    meaningless, so magnitudes are compressed before scaling.
    """
    if not values:
        return {}
    logs = {k: math.log1p(max(0.0, v)) for k, v in values.items()}
    lo, hi = min(logs.values()), max(logs.values())
    if hi <= lo:
        return {k: (100.0 if hi > 0 else 0.0) for k in logs}
    return {k: 100.0 * (v - lo) / (hi - lo) for k, v in logs.items()}


def parse_date(value):
    if not value:
        return None
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def trigger_score(triggers, as_of=None):
    """Score an account's triggers, keeping only dated, cited ones.

    An undated or uncited trigger cannot be defended in a leadership review, so it is
    dropped rather than scored at a discount.
    """
    as_of = as_of or date.today()
    best, kept = 0.0, []
    for trigger in triggers or []:
        when = parse_date(trigger.get("date"))
        url = (trigger.get("url") or "").strip()
        if not when or not url:
            continue
        age = max(0, (as_of - when).days)
        decay = 0.5 ** (age / TRIGGER_HALF_LIFE_DAYS)
        weight = TRIGGER_TYPE_WEIGHT.get(str(trigger.get("type", "other")).lower(), 0.3)
        score = 100.0 * weight * decay
        kept.append({**trigger, "ageDays": age, "score": round(score, 1)})
        best = max(best, score)
    kept.sort(key=lambda t: -t["score"])
    return best, kept


def collect(report, potential, crm=None):
    """Join the report and the sizing output into one row per account."""
    rows = []
    sized = potential.get("accounts", {})
    crm_accounts = (crm or {}).get("accounts", {}) or {}
    for account in report.get("accounts", []):
        sid = account.get("salesforceId") or ""
        key = sid or account.get("name", "")
        entry = sized.get(key, {})
        activity = account.get("activity", {}) or {}
        crm_row = crm_accounts.get(sid, {}) if sid else {}
        rows.append({
            "key": key,
            "salesforceId": sid,
            "name": account.get("name", ""),
            "play": account.get("primaryPlay", ""),
            "plays": account.get("plays", []),
            "potentialArr": float(entry.get("potentialArr") or 0),
            "lines": entry.get("lines", []),
            "aiu": entry.get("aiu", {}),
            "current": entry.get("current", {}),
            "communicationScore": float(activity.get("score") or 0),
            "twoWay": bool(activity.get("twoWay")),
            "lastActivity": activity.get("lastActivity", ""),
            "activityTier": activity.get("tier", "Unranked"),
            "renewal": account.get("renewal", ""),
            "contacts": account.get("contacts", []),
            "nextAction": account.get("nextAction", ""),
            "winPlan": account.get("winPlan", ""),
            "evidence": account.get("evidence", []),
            "discoveryGaps": account.get("discoveryGaps", []),
            "tpids": crm_row.get("tpids", []),
            "msftOverlap": bool(crm_row.get("msftOverlap")),
            "openPipeline": crm_row.get("openPipeline", []),
            "h1PipelineValue": float(crm_row.get("h1PipelineValue") or 0),
            "h1RenewalValue": float(crm_row.get("h1RenewalValue") or 0),
            "stalePipelineValue": float(crm_row.get("stalePipelineValue") or 0),
            "bestStage": crm_row.get("bestStage", ""),
            "bestStageWeight": float(crm_row.get("bestStageWeight") or 0),
        })
    return rows


def score_rows(rows, weights, triggers_by_key=None):
    pot = normalise({r["key"]: r["potentialArr"] for r in rows})
    comm = normalise({r["key"]: r["communicationScore"] for r in rows})
    # Pipeline value is discounted by how far the best live opportunity has advanced, so
    # a large deal parked at "Qualified" cannot outrank a smaller one near close.
    pipe = normalise({
        r["key"]: r.get("h1PipelineValue", 0.0) * max(r.get("bestStageWeight", 0.0), 0.3)
        for r in rows
    })
    for row in rows:
        row["potentialScore"] = round(pot.get(row["key"], 0.0), 1)
        row["commScore"] = round(comm.get(row["key"], 0.0), 1)
        composite = (weights["potential"] * row["potentialScore"]
                     + weights["communication"] * row["commScore"])
        if "pipeline" in weights:
            row["pipelineScore"] = round(pipe.get(row["key"], 0.0), 1)
            composite += weights["pipeline"] * row["pipelineScore"]
        if "trigger" in weights:
            best, kept = trigger_score((triggers_by_key or {}).get(row["key"], []))
            row["triggerScore"] = round(best, 1)
            row["triggers"] = kept
            composite += weights["trigger"] * best
        row["compositeScore"] = round(composite, 1)
    rows.sort(key=lambda r: (-r["compositeScore"], -r["potentialArr"], r["name"]))
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows


def tier_of(index, total):
    """Split the final list into three execution tiers by rank."""
    if index <= max(1, round(total * 0.25)):
        return "Tier 1 - Must win"
    if index <= max(2, round(total * 0.60)):
        return "Tier 2 - Build"
    return "Tier 3 - Develop"


def main():
    if len(sys.argv) < 5:
        raise SystemExit("usage: rank.py stage1|stage2 <report.json> <potential.json> <runDir> [opts]")

    mode, report_path, potential_path, run_dir = sys.argv[1:5]
    opts = sys.argv[5:]

    def opt(flag, cast, default):
        if flag in opts:
            try:
                return cast(opts[opts.index(flag) + 1])
            except (IndexError, ValueError):
                return default
        return default

    report = load(report_path)
    potential = load(potential_path)
    if not report or not potential:
        raise SystemExit("Cannot read report or potential JSON")

    crm_path = opt("--crm", str, os.path.join(run_dir, "crm-context.json"))
    crm = load(crm_path, {}) or {}

    rows = collect(report, potential, crm)
    os.makedirs(run_dir, exist_ok=True)

    if mode == "stage1":
        final = opt("--count", int, DEFAULT_FINAL)
        want = opt("--candidates", int, int(round(final * CANDIDATE_MULTIPLIER)))
        rows = score_rows(rows, W_STAGE1)
        # Only accounts with something to sell, and a play to sell it under, can be focus.
        eligible = [r for r in rows if r["play"] in PLAYS
                    and (r["potentialArr"] > 0 or r["communicationScore"] > 0)]
        candidates = eligible[:want]
        out = {
            "stage": 1,
            "weights": W_STAGE1,
            "eligible": len(eligible),
            "candidateCount": len(candidates),
            "targetFinalCount": final,
            "candidates": [{
                "key": r["key"], "salesforceId": r["salesforceId"], "name": r["name"],
                "play": r["play"], "potentialArr": r["potentialArr"],
                "communicationScore": r["communicationScore"],
                "compositeScore": r["compositeScore"], "rank": r["rank"],
            } for r in candidates],
        }
        dest = os.path.join(run_dir, "focus-candidates.json")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        print(json.dumps({"candidatesPath": dest, "candidates": len(candidates),
                          "eligible": len(eligible)}))
        return 0

    if mode == "stage2":
        count = max(MIN_FINAL, min(MAX_FINAL, opt("--count", int, DEFAULT_FINAL)))
        triggers_path = opt("--triggers", str, os.path.join(run_dir, "triggers.json"))
        raw_triggers = load(triggers_path, {}) or {}
        by_key = raw_triggers.get("accounts", raw_triggers)

        rows = score_rows(rows, W_STAGE2, by_key)
        eligible = [r for r in rows if r["play"] in PLAYS
                    and (r["potentialArr"] > 0 or r["communicationScore"] > 0
                         or r.get("triggerScore", 0) > 0
                         or r.get("h1PipelineValue", 0) > 0)]
        focus = eligible[:count]
        for i, row in enumerate(focus, 1):
            row["rank"] = i
            row["tier"] = tier_of(i, len(focus))

        play_mix, tier_mix = {}, {}
        for row in focus:
            play_mix[row["play"] or "Unclassified"] = play_mix.get(row["play"] or "Unclassified", 0) + 1
            tier_mix[row["tier"]] = tier_mix.get(row["tier"], 0) + 1

        out = {
            "stage": 2,
            "weights": W_STAGE2,
            "generatedAt": date.today().isoformat(),
            "selectedCount": len(focus),
            "eligible": len(eligible),
            "bookSize": len(rows),
            "triggersFound": sum(1 for r in focus if r.get("triggers")),
            "playMix": play_mix,
            "tierMix": tier_mix,
            "totals": {
                "potentialArr": round(sum(r["potentialArr"] for r in focus), 2),
                "currentArr": round(sum(float(r["current"].get("arr") or 0) for r in focus), 2),
                "withTwoWay": sum(1 for r in focus if r["twoWay"]),
                "withMsftOverlap": sum(1 for r in focus if r.get("msftOverlap")),
                "h1Pipeline": round(sum(r.get("h1PipelineValue", 0) for r in focus), 2),
                "h1Renewal": round(sum(r.get("h1RenewalValue", 0) for r in focus), 2),
            },
            "accounts": focus,
        }
        dest = os.path.join(run_dir, "focus-accounts.json")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        print(json.dumps({"focusPath": dest, "selected": len(focus),
                          "playMix": play_mix, "tierMix": tier_mix,
                          "potentialArr": out["totals"]["potentialArr"],
                          "triggersFound": out["triggersFound"]}))
        return 0

    raise SystemExit("unknown mode: %s" % mode)


if __name__ == "__main__":
    sys.exit(main())
