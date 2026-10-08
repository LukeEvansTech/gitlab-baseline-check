#!/usr/bin/env python3
"""Generate docs/docs/checks.md from baseline.json.

Run after editing baseline.json: python3 scripts/gen_checks_page.py
tests/test_docs.py fails if the page is out of date.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "baseline.json")
PAGE = os.path.join(ROOT, "docs", "docs", "checks.md")
sys.path.insert(0, ROOT)
# pylint: disable-next=wrong-import-position
from gitlab_baseline_check import fmt_expected  # noqa: E402

TIERS = {"free": "All tiers", "premium": "Premium", "ultimate": "Ultimate"}

INTRO = """\
# What it checks

This page is generated from `baseline.json`, which both scripts read. To change what
counts as a pass, edit `expect` in that file and run `python3 scripts/gen_checks_page.py`.

**Expected** shows the comparison: a plain value must match exactly, `<= n` means the
number must not exceed `n`, and `includes` means the list must contain that value.
**Tier** is the lowest licence tier on which GitLab enforces the setting. **CIS** is the
matching CIS GitLab Benchmark v1.0.1 recommendation, where there is one.

Only change the settings under "Identity after SSO" once single sign-on works, or
administrators can lock themselves out of the web interface.
"""


def cell(text):
    """Make text safe inside a Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "\\|")


def render():
    """Return the page text."""
    with open(BASELINE, encoding="utf-8") as fh:
        checks = json.load(fh)["checks"]
    out = [INTRO.rstrip("\n")]
    area = None
    for check in checks:
        if check["area"] != area:
            area = check["area"]
            out.append(f"\n## {area}\n")
            out.append("| Setting | Expected | Tier | CIS | Why |")
            out.append("| ------- | -------- | ---- | --- | --- |")
        out.append(
            f"| `{cell(check['setting'])}` | `{cell(fmt_expected(check))}` "
            f"| {TIERS[check['tier']]} | {cell(check['cis'] or '-')} | {cell(check['why'])} |"
        )
    return "\n".join(out) + "\n"


def main():
    """Write the page."""
    with open(PAGE, "w", encoding="utf-8", newline="\n") as page:
        page.write(render())
    print(f"wrote {os.path.relpath(PAGE, ROOT)}")


if __name__ == "__main__":
    main()
