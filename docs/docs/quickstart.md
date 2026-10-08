# Quick start

## 1. Get the scripts

Download the repository as a ZIP from GitHub, or clone it:

```sh
git clone https://github.com/LukeEvansTech/gitlab-baseline-check.git
```

Keep `baseline.json` in the same folder as the scripts.

## 2. Create a token

Sign in as an administrator and create a personal access token under **Edit profile > Access tokens**:

- Scopes: `read_api`, plus `admin_mode` if Admin Mode is on. Without `admin_mode` the API returns 403 when Admin Mode is on.
- Expiry: a day or two. Revoke the token when you have finished.

The token can read every admin setting, so treat it like an administrator password.

## 3. Run the check

=== "PowerShell"

    Works on Windows PowerShell 5.1 and PowerShell 7, with no modules to install.

    ```powershell
    .\Test-GitLabBaseline.ps1 -Url https://gitlab.example.com -CsvPath results.csv
    ```

    If the execution policy blocks the script:

    ```powershell
    powershell -ExecutionPolicy Bypass -File .\Test-GitLabBaseline.ps1 -Url https://gitlab.example.com
    ```

=== "Python"

    Works on Python 3.8 or later, with the standard library only.

    ```sh
    python3 gitlab_baseline_check.py --url https://gitlab.example.com --csv results.csv
    ```

    If the instance uses a certificate from an internal CA that Python doesn't trust, add `--ca-bundle path/to/ca.pem`.

The script prompts for the token without echoing it. To run unattended, set the `GITLAB_TOKEN` environment variable instead. Never pass the token as a command-line argument.

The URL must start with `https://`. The scripts refuse redirects, so use the instance's final address, not one that redirects to it.

## 4. Read the output

The console shows one line per setting and a summary. The CSV adds the area, tier, CIS reference and the reason for each setting. See [Reading the results](results.md).
