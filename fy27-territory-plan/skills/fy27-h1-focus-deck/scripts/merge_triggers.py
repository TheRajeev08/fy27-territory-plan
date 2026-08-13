"""Merge and validate trigger JSON returned by the research sub-agents.

    python3 merge_triggers.py <focus-candidates.json> <trigger-dir> <out.json>

Agents return one JSON blob per batch, often wrapped in markdown fences and often
keyed by whatever identifier they found easiest (Salesforce id, account name, or
the plan's own key). This normalises all of that onto the candidate key, and
enforces the evidence bar the deck promises: every trigger must carry a known
type, an ISO date, and an http source URL. Anything that fails is dropped rather
than discounted, and the drop count is reported so a bad batch is visible.
"""
import glob
import json
import os
import re
import sys

# Must stay in step with TRIGGER_TYPE_WEIGHT in rank.py — a type this file accepts
# but rank.py does not know scores at the "other" floor, and a type rank.py knows
# but this file rejects is silently lost.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from rank import TRIGGER_TYPE_WEIGHT
    VALID = set(TRIGGER_TYPE_WEIGHT)
except Exception:
    VALID = {"funding", "acquisition", "security_incident", "leadership_change",
             "ai_launch", "product_launch", "expansion", "partnership",
             "earnings", "recognition", "other"}

FIELDS = ("type", "date", "headline", "url", "soWhat")


def main(candidates_path, trigger_dir, out_path):
    with open(candidates_path, "r", encoding="utf-8") as fh:
        candidates = json.load(fh)
    accounts = (candidates.get("candidates") or candidates.get("accounts")
                or (candidates if isinstance(candidates, list) else []))
    by_sf = {a["salesforceId"]: a for a in accounts if a.get("salesforceId")}
    by_name = {str(a.get("name", "")).strip().lower(): a for a in accounts}
    by_key = {a["key"]: a for a in accounts if a.get("key")}

    out, dropped, unmatched = {}, 0, []
    for path in sorted(glob.glob(os.path.join(trigger_dir, "*.json"))):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read().strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            continue
        try:
            payload = json.loads(match.group(0)).get("accounts", {})
        except json.JSONDecodeError:
            continue
        for raw_key, items in payload.items():
            account = (by_sf.get(raw_key) or by_name.get(str(raw_key).strip().lower())
                       or by_key.get(raw_key))
            if not account:
                unmatched.append(raw_key)
                continue
            keep = []
            for trigger in items or []:
                if (str(trigger.get("type", "")).lower() in VALID
                        and re.match(r"^\d{4}-\d{2}-\d{2}$", str(trigger.get("date", "")))
                        and str(trigger.get("url", "")).startswith("http")):
                    keep.append({k: trigger[k] for k in FIELDS if k in trigger})
                else:
                    dropped += 1
            if keep:
                out.setdefault(account["key"], []).extend(keep)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"accounts": out}, fh, indent=1)
    print(json.dumps({
        "path": out_path,
        "accountsWithTriggers": len(out),
        "triggers": sum(len(v) for v in out.values()),
        "dropped": dropped,
        "unmatchedKeys": unmatched[:10],
    }))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
