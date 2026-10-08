#!/usr/bin/env python3
"""Read-only check of a GitLab self-managed instance against baseline.json.

Reads GET /api/v4/application/settings, the licence and the version, then compares each
setting in baseline.json with the instance. It never changes anything on the instance and
prints only the settings it checks.

The token comes from the GITLAB_TOKEN environment variable, or a hidden prompt.
It needs an administrator's token with the read_api scope, plus admin_mode when Admin Mode
is on. Standard library only; Python 3.8 or later.
"""

import argparse
import csv
import getpass
import http.client
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RANK = {"free": 0, "premium": 1, "ultimate": 2}
# Older licence names map to the tier that replaced them.
PLAN_ALIASES = {
    "silver": "premium",
    "gold": "ultimate",
    "bronze": "free",
    "starter": "free",
}
COLUMNS = ["result", "area", "setting", "expected", "actual", "tier", "cis", "why"]


class ApiError(Exception):
    """An API call failed in a way that stops the check."""


def fmt(value):
    """Render a value the same way the PowerShell checker does."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, list):
        return ";".join(fmt(v) for v in value) or "(empty)"
    return str(value)


def fmt_expected(check):
    """Render the expected value with its comparison."""
    op, want = check["op"], check["expect"]
    if op == "le":
        return "<= " + fmt(want)
    if op == "contains":
        return "includes " + fmt(want)
    return fmt(want)


def kind(value):
    """Classify a JSON value so both checkers compare like with like."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    return "other"


def matches(op, want, have):
    """Compare the same way the PowerShell checker does: by kind and rendered value."""
    if op == "eq":
        return kind(have) == kind(want) and fmt(have) == fmt(want)
    if op == "le":
        return kind(have) == "number" and have <= want
    if op == "contains":
        return isinstance(have, list) and all(w in have for w in want)
    raise ValueError("unknown op " + op)


def evaluate(checks, settings, plan):
    """Return one result row per check. plan is free, premium or ultimate."""
    rows = []
    for check in checks:
        name = check["setting"]
        if name not in settings:
            result, actual = "ABSENT", "(absent)"
        else:
            have = settings[name]
            actual = fmt(have)
            if not matches(check["op"], check["expect"], have):
                result = "FAIL"
            elif RANK[plan] < RANK[check["tier"]]:
                result = "NOT ENFORCED"
            else:
                result = "PASS"
        rows.append(
            {
                "result": result,
                "area": check["area"],
                "setting": name,
                "expected": fmt_expected(check),
                "actual": actual,
                "tier": check["tier"],
                "cis": check["cis"],
                "why": check["why"],
            }
        )
    return rows


def normalise_plan(plan):
    """Map a licence plan name to free, premium or ultimate."""
    plan = PLAN_ALIASES.get((plan or "free").lower(), (plan or "free").lower())
    return plan if plan in RANK else "free"


def licence_plan(lic):
    """Return the tier a licence enforces.

    An expired trial turns paid features off and an expired paid licence does not, but
    the licence API does not say which one it is. Treat any expired licence as Free, so
    a paid-tier setting can show NOT ENFORCED wrongly but never PASS wrongly.
    """
    plan = normalise_plan(lic.get("plan"))
    if lic.get("expired"):
        print(
            f"warning: the {plan} licence has expired, so paid-tier settings are "
            "checked as Free. If it was a paid licence, not a trial, they may still apply.",
            file=sys.stderr,
        )
        return "free"
    return plan


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse every redirect, so the token is never sent to another URL."""

    # pylint: disable-next=unused-argument,too-many-arguments,too-many-positional-arguments
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:  # pylint: disable=too-few-public-methods
    """Minimal GET-only GitLab API client."""

    def __init__(self, url, token, ca_bundle=None):
        if not url.lower().startswith("https://"):
            raise ApiError(
                "the URL must start with https://, so the token is encrypted."
            )
        # Header errors quote the value, so reject a malformed token before any request.
        if not re.fullmatch(r"[\x21-\x7e]+", token):
            raise ApiError(
                "the token contains spaces, line breaks or other invalid characters."
            )
        self.base = url.rstrip("/") + "/api/v4"
        self.token = token
        self.opener = urllib.request.build_opener(
            NoRedirect(),
            urllib.request.HTTPSHandler(
                context=ssl.create_default_context(cafile=ca_bundle)
            ),
        )

    def get(self, path):
        """Return (status, parsed JSON). The body is None on an HTTP error."""
        req = urllib.request.Request(self.base + path)
        req.add_header("PRIVATE-TOKEN", self.token)
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as err:
            if 300 <= err.code < 400:
                raise ApiError(
                    f"GET {path} was redirected (HTTP {err.code}) and the redirect was "
                    "refused. Pass the instance's final https:// URL."
                ) from err
            return err.code, None
        except urllib.error.URLError as err:
            raise ApiError(f"cannot reach {self.base}: {err.reason}") from err
        except (OSError, ValueError, http.client.HTTPException) as err:
            raise ApiError(f"GET {path} gave an unreadable response: {err}") from err


def fetch(client):
    """Return (settings, plan, version) from a live instance."""
    status, settings = client.get("/application/settings")
    if status == 401:
        raise ApiError("401 Unauthorized: the token is invalid, expired or revoked.")
    if status == 403:
        raise ApiError(
            "403 Forbidden: the token must belong to an administrator. If Admin Mode is on, "
            "the token also needs the admin_mode scope."
        )
    if status != 200 or not isinstance(settings, dict):
        raise ApiError(f"GET /application/settings returned HTTP {status}.")
    status, meta = client.get("/metadata")
    if status != 200 or not isinstance(meta, dict):
        status, meta = client.get("/version")
    version = (meta or {}).get("version", "unknown")
    enterprise = (meta or {}).get("enterprise")
    status, lic = client.get("/license")
    # Community Edition has no licence endpoint (404); Enterprise without a licence
    # returns null. Any other failure leaves the tier unknown, so stop.
    if enterprise is False or status == 404 or (status == 200 and lic is None):
        plan = "free"
    elif status == 200 and isinstance(lic, dict):
        plan = licence_plan(lic)
    else:
        raise ApiError(f"GET /license returned HTTP {status}, so the tier is unknown.")
    return settings, plan, version


def print_table(rows, plan, version):
    """Print the results as a fixed-width table with a summary line."""
    print(f"GitLab {version}, licence tier: {plan}\n")
    width = max(len(r["setting"]) for r in rows)
    print(f"{'RESULT':13} {'SETTING':{width}} {'EXPECTED':>18} {'ACTUAL':>18}")
    for r in rows:
        line = f"{r['result']:13} {r['setting']:{width}} {r['expected']:>18}"
        print(f"{line} {r['actual']:>18}")
    kinds = ("PASS", "FAIL", "NOT ENFORCED", "ABSENT")
    counts = {k: sum(r["result"] == k for r in rows) for k in kinds}
    print(
        f"\n{counts['PASS']} of {len(rows)} pass, {counts['FAIL']} fail, "
        f"{counts['NOT ENFORCED']} set but not enforced on {plan}, {counts['ABSENT']} absent"
    )


def write_csv(rows, path):
    """Write the results as CSV, matching the PowerShell output byte for byte."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    """Run the check and return the exit code."""
    parser = argparse.ArgumentParser(
        description="Read-only check of a GitLab instance against baseline.json."
    )
    parser.add_argument(
        "--url", help="instance URL, for example https://gitlab.example.com"
    )
    parser.add_argument("--csv", help="also write the results to this CSV file")
    parser.add_argument("--baseline", default=os.path.join(HERE, "baseline.json"))
    parser.add_argument(
        "--ca-bundle", help="PEM file of CA certificates, for an internal CA"
    )
    parser.add_argument(
        "--from-file",
        help="test mode: read {plan, version, settings} JSON instead of calling an instance",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.baseline, encoding="utf-8") as fh:
            checks = json.load(fh)["checks"]
        if args.from_file:
            with open(args.from_file, encoding="utf-8") as fh:
                data = json.load(fh)
            settings, plan, version = (
                data["settings"],
                normalise_plan(data["plan"]),
                data["version"],
            )
        else:
            if not args.url:
                parser.error("--url is required")
            token = os.environ.get("GITLAB_TOKEN") or getpass.getpass("GitLab token: ")
            settings, plan, version = fetch(
                Client(args.url, token.strip(), args.ca_bundle)
            )
        rows = evaluate(checks, settings, plan)
        print_table(rows, plan, version)
        if args.csv:
            write_csv(rows, args.csv)
    except (ApiError, OSError, ValueError, KeyError, TypeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.csv:
        print(f"wrote {args.csv}")
    return 0 if all(r["result"] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
