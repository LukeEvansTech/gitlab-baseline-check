# gitlab-baseline-check

A read-only check of a GitLab self-managed instance's instance-wide security settings against a baseline. The same check comes as a Python script and a PowerShell script, so it runs on whatever machine you have.

Both scripts read `baseline.json`, call the GitLab REST API with GET requests only, and print one line per setting. They change nothing on the instance.

## What it checks

`baseline.json` lists 31 settings from **Admin > Settings**: Admin Mode, session lifetime, sign-up, dormant accounts, who can create groups and projects, default visibility, token expiry, OAuth applications, outbound requests from webhooks, admin exports, and password and two-factor sign-in. Where a setting maps to a CIS GitLab Benchmark v1.0.1 recommendation, the `cis` field gives its number.

The check also reads the licence. GitLab saves some settings on any tier but enforces them only on a paid one. On Free, the 90-day token lifetime cap reads back as 90 and GitLab still issues a 365-day token. The check reports a setting like that as `NOT ENFORCED`, not `PASS`.

An expired licence counts as Free, because the API doesn't say whether it was a trial, and an expired trial turns paid features off.

The five settings under "Identity after SSO" turn off password sign-in and require two-factor authentication. Only change them once single sign-on works, or administrators can lock themselves out.

The check covers instance settings only. Group and project controls, such as protected branches, merge request approvals and push rules, need checking separately.

## Before you run it

You need:

- An administrator's personal access token with the `read_api` scope. If Admin Mode is on, the token also needs the `admin_mode` scope; without it the API returns 403. Set an expiry of a day or two and revoke the token afterwards.
- Python 3.8 or later, or Windows PowerShell 5.1, or PowerShell 7. Neither script needs extra packages or modules.

Both scripts only accept an `https://` URL and refuse redirects, so the token is never sent unencrypted or to another host. The scripts read the token from the `GITLAB_TOKEN` environment variable. If it isn't set, they prompt for it without echoing. Never pass the token as a command-line argument.

## Run it

PowerShell:

```powershell
.\Test-GitLabBaseline.ps1 -Url https://gitlab.example.com -CsvPath results.csv
```

If the execution policy blocks the script, run it with `powershell -ExecutionPolicy Bypass -File .\Test-GitLabBaseline.ps1 -Url …`.

Python:

```sh
python3 gitlab_baseline_check.py --url https://gitlab.example.com --csv results.csv
```

If the instance uses a certificate from an internal CA that Python doesn't trust, add `--ca-bundle path/to/ca.pem`. PowerShell uses the Windows certificate store.

## Read the results

| Result         | Meaning                                                                 |
| -------------- | ----------------------------------------------------------------------- |
| `PASS`         | The setting matches the baseline and the licence tier enforces it.      |
| `FAIL`         | The setting does not match the baseline.                                |
| `NOT ENFORCED` | The setting matches, but the instance's tier is below the one it needs. |
| `ABSENT`       | The API did not return the setting, usually because of the version.     |

Exit code 0 means every setting passed, 1 means at least one did not, and 2 means the check could not run.

The CSV has the same rows plus the tier, CIS reference and the reason for each setting. It records your instance's security configuration, so store and share it accordingly. The repository ignores `*.csv` so a result is not committed by mistake.

## Change the baseline

Edit `expect` in `baseline.json`. `op` is `eq` for an exact match, `le` for a number that must not exceed the value, and `contains` for a list that must include every listed value. `tier` is the lowest tier that enforces the setting: `free`, `premium` or `ultimate`.

## Tests

`tests/test_parity.py` runs both scripts against a fixture of edge cases and requires the same CSV, byte for byte, from each. CI runs it on Linux with PowerShell 7 and on Windows with both Windows PowerShell 5.1 and PowerShell 7.

```sh
python3 -m unittest discover -s tests -v
```

## Licence

MIT
