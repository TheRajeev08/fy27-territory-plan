"""Final-state gate for one FY27 run: prove the artefacts are right, not just present.

    python3 verify_run.py <runDir> [--json]

Why this exists
---------------
The pipeline degrades quietly. When ``licensing.json`` is missing, ``workbook.py`` still writes a
perfectly valid workbook - it just swaps the GHCP sprint queue for a narrower rank-ordered one and
carries on with a zero exit code. The run *looks* finished. The teammate finds out when their
sales leader asks where the Copilot seat-expansion list went.

Everything checked here is a thing that has actually gone wrong at least once: the fallback sprint
layout, the priority-accounts block silently absent from the sheet, an override that matched no
account because the name was typo'd, an undated trigger, a coverage denominator that never got set.

FAIL means the run is not shippable. WARN means it is shippable but thin, and the thinness should
be stated out loud rather than discovered on the slide.
"""
import json
import os
import re
import sys
import zipfile

WORKBOOK = "FY27 Territory Plan.xlsx"
LEADERSHIP_DECK = "fy27-h1-leadership.pptx"
EVIDENCE_DECK = "fy27-h1-focus-accounts.pptx"
EVIDENCE_WORKBOOK = "fy27-h1-focus-accounts.xlsx"

# Written only by the GHCP layout. The fallback layouts title the sheet "MEETING BOOKING QUEUE".
GHCP_SHEET_MARKER = "SPRINT FOCUS - GHCP BOOKING QUEUE"
PRIORITY_MARKER = "PRIORITY ACCOUNTS"
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
TAG_RE = re.compile(r"<[^>]+>")


class Report:
    def __init__(self):
        self.checks = []

    def add(self, status, name, detail):
        self.checks.append({"check": name, "status": status, "detail": detail})

    def ok(self, name, detail):
        self.add("PASS", name, detail)

    def warn(self, name, detail):
        self.add("WARN", name, detail)

    def fail(self, name, detail):
        self.add("FAIL", name, detail)

    @property
    def failed(self):
        return [c for c in self.checks if c["status"] == "FAIL"]

    @property
    def warned(self):
        return [c for c in self.checks if c["status"] == "WARN"]


def read_json(run_dir, name):
    try:
        with open(os.path.join(run_dir, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def xlsx_text(path):
    """Every string in a workbook, tags stripped. Covers both shared and inline strings."""
    chunks = []
    try:
        with zipfile.ZipFile(path) as zf:
            for entry in zf.namelist():
                if not entry.startswith("xl/") or not entry.endswith(".xml"):
                    continue
                if not (entry == "xl/sharedStrings.xml" or entry.startswith("xl/worksheets/")):
                    continue
                chunks.append(TAG_RE.sub(" ", zf.read(entry).decode("utf-8", "replace")))
    except (OSError, zipfile.BadZipFile, KeyError):
        return None
    return " ".join(chunks)


def check_artefacts(run_dir, report):
    for name, label in ((WORKBOOK, "territory workbook"),
                        (LEADERSHIP_DECK, "leadership deck"),
                        (EVIDENCE_DECK, "evidence deck"),
                        (EVIDENCE_WORKBOOK, "evidence workbook")):
        path = os.path.join(run_dir, name)
        if not os.path.isfile(path):
            report.fail("artefact:" + name, "missing - the %s was never built" % label)
        elif os.path.getsize(path) < 4096:
            report.fail("artefact:" + name, "only %d bytes - truncated or empty"
                        % os.path.getsize(path))
        else:
            report.ok("artefact:" + name, "%.0f KB" % (os.path.getsize(path) / 1024.0))


def check_sprint_layout(run_dir, report):
    """The sprint queue is the GHCP priority. A fallback layout is a failure, not a variant."""
    licensing = read_json(run_dir, "licensing.json") or {}
    lic_accounts = licensing.get("accounts") or {}
    if not lic_accounts:
        report.fail("sprint:licensing",
                    "licensing.json is missing or empty, so the GHCP segmentation cannot be "
                    "computed. Re-run licensing.py, then rebuild the workbook with "
                    "workbook.py --from-report.")
    else:
        report.ok("sprint:licensing", "%d account(s) with live licensing" % len(lic_accounts))

    path = os.path.join(run_dir, WORKBOOK)
    if not os.path.isfile(path):
        return
    text = xlsx_text(path)
    if text is None:
        report.fail("sprint:layout", "could not read %s as a workbook" % WORKBOOK)
        return
    if GHCP_SHEET_MARKER in text:
        report.ok("sprint:layout", "Sprint Focus is in the GHCP layout")
    else:
        report.fail("sprint:layout",
                    "Sprint Focus fell back to the rank-ordered layout - the GHCP segments "
                    "(seat expansion / AIU activation / land GHE first) are not in the sheet. "
                    "This happens when the workbook is rebuilt before licensing lands.")
    if PRIORITY_MARKER in text:
        report.ok("sprint:priority", "priority accounts listed above the queue")
    else:
        report.fail("sprint:priority",
                    "the priority-accounts block is absent from the Sprint Focus sheet - "
                    "no Tier 1 accounts were carried, so there is nothing to work top-down.")


def check_coverage(run_dir, report):
    coverage = read_json(run_dir, "coverage.json")
    if not coverage:
        report.fail("coverage:file", "coverage.json missing - targets.py never ran, so the deck "
                                     "has no quota denominator and renders $0 / TBD throughout.")
        return
    buckets = coverage.get("buckets") or []
    known = [b for b in buckets
             if b.get("targetKnown") or b.get("h1Target") is not None]
    if not known:
        report.warn("coverage:targets",
                    "no bucket carries a target, so every coverage figure renders TBD. "
                    "Set them in the seller profile if you want coverage on the deck.")
    else:
        report.ok("coverage:targets", "%d of %d bucket(s) have a target"
                  % (len(known), len(buckets)))
    territory = (coverage.get("territory") or "").strip()
    if territory:
        report.ok("coverage:territory", "title slide reads '%s'" % territory)
    else:
        report.warn("coverage:territory",
                    "no territory set - the title slide omits the geo.")


def check_overrides(run_dir, report):
    potential = read_json(run_dir, "potential.json") or {}
    unmatched = potential.get("overridesUnmatched") or []
    if unmatched:
        report.fail("overrides:matched",
                    "%d override(s) matched no account and were silently ignored: %s. "
                    "Check the spelling against the account names in the plan."
                    % (len(unmatched), ", ".join(str(u) for u in unmatched[:8])))
    else:
        report.ok("overrides:matched", "every override matched an account")


def check_triggers(run_dir, report):
    focus = read_json(run_dir, "focus-accounts.json")
    if not focus:
        report.fail("focus:file", "focus-accounts.json missing - no H1 focus set was ranked.")
        return
    accounts = focus.get("accounts") or []
    if not accounts:
        report.fail("focus:accounts", "the focus set is empty.")
        return

    undated, with_trigger = [], 0
    for account in accounts:
        triggers = account.get("triggers") or []
        if triggers:
            with_trigger += 1
        for trigger in triggers:
            if not isinstance(trigger, dict):
                continue
            if not DATE_RE.search(str(trigger.get("date") or "")):
                undated.append("%s: %s" % (account.get("name", "?"),
                                           str(trigger.get("headline", ""))[:60]))

    report.ok("focus:accounts", "%d focus account(s)" % len(accounts))
    if undated:
        report.fail("focus:triggerDates",
                    "%d trigger(s) carry no date and must be dropped or dated: %s"
                    % (len(undated), "; ".join(undated[:5])))
    else:
        report.ok("focus:triggerDates", "every trigger is dated")

    without = len(accounts) - with_trigger
    if without:
        report.warn("focus:triggerCoverage",
                    "%d of %d focus account(s) carry no dated trigger - say so rather than "
                    "implying a live signal." % (without, len(accounts)))
    else:
        report.ok("focus:triggerCoverage", "every focus account carries a dated trigger")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    positional = [a for a in args if not a.startswith("--")]
    if not positional:
        print(__doc__)
        return 2
    run_dir = positional[0]
    if not os.path.isdir(run_dir):
        print("verify_run: no such run directory %s" % run_dir, file=sys.stderr)
        return 2

    report = Report()
    check_artefacts(run_dir, report)
    check_sprint_layout(run_dir, report)
    check_coverage(run_dir, report)
    check_overrides(run_dir, report)
    check_triggers(run_dir, report)

    payload = {
        "runDir": run_dir,
        "ok": not report.failed,
        "failures": len(report.failed),
        "warnings": len(report.warned),
        "checks": report.checks,
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for check in report.checks:
            print("%-4s %-24s %s" % (check["status"], check["check"], check["detail"]))
        print()
        print("%s - %d failure(s), %d warning(s)"
              % ("SHIPPABLE" if not report.failed else "NOT SHIPPABLE",
                 len(report.failed), len(report.warned)))
    return 0 if not report.failed else 1


if __name__ == "__main__":
    sys.exit(main())
