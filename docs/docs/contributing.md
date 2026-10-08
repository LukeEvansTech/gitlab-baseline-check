# Contributing

Issues and pull requests are welcome on [GitHub](https://github.com/LukeEvansTech/gitlab-baseline-check).

## Change the baseline

1. Edit `baseline.json`. `op` is `eq` for an exact match, `le` for a number that must not exceed the value, and `contains` for a list that must include every listed value. `tier` is the lowest tier that enforces the setting: `free`, `premium` or `ultimate`.
2. Run `python3 scripts/gen_checks_page.py` to regenerate [What it checks](checks.md).
3. If the change affects the edge-case fixture, regenerate the expected CSV with `python3 gitlab_baseline_check.py --from-file tests/fixtures/edge-cases.json --csv tests/fixtures/edge-cases.expected.csv`.

## Keep the two scripts in step

Both scripts must produce the same CSV, byte for byte. Any change to how one compares or formats values needs the same change in the other.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The parity test runs both scripts against `tests/fixtures/edge-cases.json` and compares each CSV with the expected one. Set `BASELINE_PS=powershell` to test Windows PowerShell 5.1 instead of `pwsh`. CI runs it on Linux with PowerShell 7 and on Windows with both. A second test fails if the checks page is out of date.

## Preview the docs

```sh
cd docs
pip install -r requirements.txt
zensical serve
```
