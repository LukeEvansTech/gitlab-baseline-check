# gitlab-baseline-check

A read-only check of a GitLab self-managed instance's instance-wide security settings against a baseline, as a PowerShell script and a Python script that give identical results.

**Documentation: <https://lukeevanstech.github.io/gitlab-baseline-check/>**

Both scripts read `baseline.json`, call the GitLab REST API with GET requests only, and change nothing on the instance. They read the licence too, so a setting GitLab saves but doesn't enforce on the instance's tier shows as `NOT ENFORCED`, not `PASS`.

## Quick start

You need an administrator's personal access token with the `read_api` scope, plus `admin_mode` if Admin Mode is on. The scripts read it from `GITLAB_TOKEN` or prompt for it without echoing.

```powershell
.\Test-GitLabBaseline.ps1 -Url https://gitlab.example.com -CsvPath results.csv
```

```sh
python3 gitlab_baseline_check.py --url https://gitlab.example.com --csv results.csv
```

PowerShell 5.1 or 7, or Python 3.8 or later. Neither needs extra modules or packages.

Exit code 0 means every setting passed, 1 means at least one did not, and 2 means the check could not run.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## Licence

MIT
