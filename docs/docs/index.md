# GitLab Baseline Check

A read-only check of a GitLab self-managed instance's instance-wide security settings against a baseline. The same check comes as a PowerShell script and a Python script, so it runs on whatever machine the person running it has.

Both scripts read the same `baseline.json`, call the GitLab REST API with GET requests only, and print one line per setting. They change nothing on the instance, and they print only the settings in the baseline, never the rest of the settings response.

```text
GitLab 19.4.1-ee, licence tier: free

RESULT        SETTING                                      EXPECTED             ACTUAL
PASS          admin_mode                                       true               true
PASS          session_expire_delay                           <= 480                480
NOT ENFORCED  max_personal_access_token_lifetime              <= 90                 90
FAIL          require_two_factor_authentication                true              false
...

25 of 31 pass, 5 fail, 1 set but not enforced on free, 0 absent
```

## Why the licence tier matters

GitLab saves some settings on any tier but only enforces them on a paid one. On Free, the 90-day token lifetime cap reads back as 90, yet GitLab still issues a 365-day token. An audit that only reads settings would call that control in place. This check reads the licence too and reports such a setting as `NOT ENFORCED`, not `PASS`.

## What it covers

The 31 settings under **Admin > Settings** that set the instance's security floor: Admin Mode, session lifetime, sign-up, dormant accounts, who can create groups and projects, default visibility, token expiry, OAuth applications, outbound requests from webhooks, admin exports, and password and two-factor sign-in. [What it checks](checks.md) lists each one.

Group and project controls, such as protected branches, merge request approvals and push rules, are out of scope and need checking separately.

## Next steps

- [Quick start](quickstart.md): create a token and run the check.
- [Reading the results](results.md): what each result and exit code means.
- [Troubleshooting](troubleshooting.md): error messages and what to do about them.
