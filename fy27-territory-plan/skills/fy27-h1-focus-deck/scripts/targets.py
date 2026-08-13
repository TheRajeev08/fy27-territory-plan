"""Compute target coverage: what the number is, what is committed, and what is missing.

    python3 targets.py <potential.json> <focus-accounts.json> <runDir>
        [--targets targets.json] [--crm crm-context.json]

Writes coverage.json. This is the arithmetic behind the "how will you achieve it"
slide, and it is deliberately conservative:

  * Renewals never count towards attainment or gap. The targets are net-new, so
    folding renewals in would show coverage the plan has not earned. They are
    reported separately because leadership will ask.
  * Sized potential is TAM, not commit. It is reported in its own column and never
    added to pipeline, because summing an aspiration with a dated opportunity
    produces a number that means nothing.
  * A null target renders as TBD with the percentage suppressed. Inventing a
    denominator to make a chart look complete would misstate attainment.

Bucket 1 is GHE + GHAS. Bucket 2 is consumption: Copilot/AIU, Actions, Codespaces
and Code Quality. The sized lines in potential.json use the product vocabulary
"Copilot" / "GHAS" / "GHE", so the mapping below is what joins the two worlds.
"""
import json
import os
import sys

QUARTERS = ("Q1", "Q2")

# potential.json product -> bucket. Anything unmapped falls to Bucket 2 (consumption),
# which is the safer default: it keeps unknown products out of the quota-bearing
# Bucket 1 number rather than silently inflating it.
PRODUCT_BUCKET = {
    "GHE": "Bucket 1",
    "GHAS": "Bucket 1",
    "Copilot": "Bucket 2",
    "AIU": "Bucket 2",
    "Actions": "Bucket 2",
    "Codespaces": "Bucket 2",
    "Code Quality": "Bucket 2",
}


def load(path, default=None):
    if not path or not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def bucket_of(product):
    return PRODUCT_BUCKET.get(product, "Bucket 2")


def sized_by_product(focus):
    """Sized potential for the focus set, per product, from the selected accounts only."""
    out = {}
    for acct in focus.get("accounts", []):
        for line in acct.get("lines", []):
            out[line["product"]] = out.get(line["product"], 0.0) + float(line.get("value") or 0)
    return out


def pipeline_totals(crm, focus):
    """H1 open pipeline for the focus set, split net-new vs renewal vs stale."""
    if not crm:
        return {"netNew": 0.0, "renewal": 0.0, "stale": 0.0, "accounts": 0,
                "staleCount": 0, "byAccount": {}}
    accounts = crm.get("accounts", {})
    ids = {a.get("salesforceId") for a in focus.get("accounts", []) if a.get("salesforceId")}
    net = ren = stale = 0.0
    stale_count = 0
    by_account = {}
    for sid in ids:
        rec = accounts.get(sid)
        if not rec:
            continue
        net += rec.get("h1PipelineValue", 0.0)
        ren += rec.get("h1RenewalValue", 0.0)
        stale += rec.get("stalePipelineValue", 0.0)
        stale_count += sum(1 for o in rec.get("openPipeline", []) if o.get("stale"))
        if rec.get("h1PipelineValue", 0.0) > 0:
            by_account[sid] = rec["h1PipelineValue"]
    return {"netNew": round(net, 2), "renewal": round(ren, 2), "stale": round(stale, 2),
            "accounts": len(by_account), "staleCount": stale_count, "byAccount": by_account}


def build(targets, potential, focus, crm):
    sized = sized_by_product(focus)
    pipe = pipeline_totals(crm, focus)

    buckets = []
    for name, cfg in targets.get("buckets", {}).items():
        lines = []
        bucket_target_h1 = 0.0
        bucket_known = True
        for product, quarters in cfg.get("targets", {}).items():
            q = {qtr: quarters.get(qtr) for qtr in QUARTERS}
            known = all(q[qtr] is not None for qtr in QUARTERS)
            h1 = sum(q[qtr] for qtr in QUARTERS) if known else None
            if known:
                bucket_target_h1 += h1
            else:
                bucket_known = False
            lines.append({
                "product": product,
                "quarters": q,
                "h1Target": h1,
                "targetKnown": known,
            })

        # Sized TAM for this bucket, from the focus set.
        bucket_sized = round(sum(v for p, v in sized.items() if bucket_of(p) == name), 2)
        attained = cfg.get("attained", {})
        attained_h1 = sum(float(attained.get(qtr) or 0) for qtr in QUARTERS)

        gap = round(bucket_target_h1 - attained_h1, 2) if bucket_known else None
        coverage = (round(bucket_sized / bucket_target_h1, 2)
                    if bucket_known and bucket_target_h1 else None)

        buckets.append({
            "bucket": name,
            "label": cfg.get("label", name),
            "products": cfg.get("products", []),
            "lines": lines,
            "h1Target": round(bucket_target_h1, 2) if bucket_known else None,
            "targetKnown": bucket_known,
            "attained": {qtr: float(attained.get(qtr) or 0) for qtr in QUARTERS},
            "attainedH1": round(attained_h1, 2),
            "gap": gap,
            "attainmentPct": (round(100.0 * attained_h1 / bucket_target_h1, 1)
                              if bucket_known and bucket_target_h1 else None),
            "sizedPotential": bucket_sized,
            "coverageRatio": coverage,
        })

    # Per-product coverage inside Bucket 1 is the detail that carries the story: the
    # bucket can look covered in aggregate while one product is badly short.
    product_rows = []
    for bucket in buckets:
        for line in bucket["lines"]:
            product = line["product"]
            tam = round(sized.get(product, 0.0), 2) if product in sized else None
            if product == "Consumption":
                tam = round(sum(v for p, v in sized.items() if bucket_of(p) == "Bucket 2"), 2)
            product_rows.append({
                "bucket": bucket["bucket"],
                "product": product,
                "q1Target": line["quarters"]["Q1"],
                "q2Target": line["quarters"]["Q2"],
                "h1Target": line["h1Target"],
                "targetKnown": line["targetKnown"],
                "sizedPotential": tam,
                "coverageRatio": (round(tam / line["h1Target"], 2)
                                  if line["targetKnown"] and line["h1Target"] and tam
                                  else None),
            })

    known_targets = [b for b in buckets if b["targetKnown"]]
    return {
        "fiscalYear": targets.get("fiscalYear", ""),
        "half": targets.get("half", ""),
        "basis": targets.get("basis", "net-new"),
        "buckets": buckets,
        "products": product_rows,
        "pipeline": pipe,
        "totals": {
            "h1Target": round(sum(b["h1Target"] for b in known_targets), 2),
            "attainedH1": round(sum(b["attainedH1"] for b in buckets), 2),
            "gap": round(sum(b["gap"] for b in known_targets), 2),
            "sizedPotential": round(sum(b["sizedPotential"] for b in buckets), 2),
            "targetsComplete": len(known_targets) == len(buckets),
        },
    }


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    potential_path, focus_path, run_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    args = sys.argv[4:]

    def opt(flag, default):
        return args[args.index(flag) + 1] if flag in args else default

    targets_path = opt("--targets", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 "targets.json"))
    crm_path = opt("--crm", os.path.join(run_dir, "crm-context.json"))

    targets = load(targets_path)
    if not targets:
        raise SystemExit("targets file not found: %s" % targets_path)

    result = build(targets, load(potential_path, {}), load(focus_path, {}), load(crm_path))
    out = os.path.join(run_dir, "coverage.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)

    print(json.dumps({
        "coveragePath": out,
        "h1Target": result["totals"]["h1Target"],
        "attainedH1": result["totals"]["attainedH1"],
        "gap": result["totals"]["gap"],
        "targetsComplete": result["totals"]["targetsComplete"],
        "h1NetNewPipeline": result["pipeline"]["netNew"],
        "h1RenewalPipeline": result["pipeline"]["renewal"],
        "coverageByProduct": {r["product"]: r["coverageRatio"] for r in result["products"]},
    }))


if __name__ == "__main__":
    main()
