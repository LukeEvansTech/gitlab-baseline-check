# Reading the results

## Results

| Result         | Meaning                                                                          |
| -------------- | -------------------------------------------------------------------------------- |
| `PASS`         | The setting matches the baseline, and the licence tier enforces it.              |
| `FAIL`         | The setting does not match the baseline.                                         |
| `NOT ENFORCED` | The setting matches, but the instance's tier is below the one that enforces it.  |
| `ABSENT`       | The API did not return the setting, usually because the GitLab version is older. |

A `NOT ENFORCED` result means GitLab ignores the setting even though it reads correctly. Close the gap with a licence upgrade or a compensating control.

An expired licence counts as Free. The licence API doesn't say whether a licence was a trial, and an expired trial turns paid features off. The script prints a warning when this happens; if the expired licence was a paid one, its paid-tier settings may still apply.

## Exit codes

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| `0`  | Every setting passed.                                |
| `1`  | The check ran and at least one setting did not pass. |
| `2`  | The check could not run. The error message says why. |

## The CSV

With `-CsvPath` or `--csv`, the script also writes a CSV with these columns:

| Column     | Content                                                   |
| ---------- | --------------------------------------------------------- |
| `result`   | `PASS`, `FAIL`, `NOT ENFORCED` or `ABSENT`                |
| `area`     | The group the setting belongs to                          |
| `setting`  | The API field name                                        |
| `expected` | The baseline value and comparison                         |
| `actual`   | The instance's value                                      |
| `tier`     | The lowest tier that enforces the setting                 |
| `cis`      | The CIS GitLab Benchmark v1.0.1 recommendation, if any    |
| `why`      | What the setting does and why the baseline value is safer |

The two scripts write the same CSV byte for byte, so you can compare results from either.

The CSV records an instance's security configuration. Store and share it accordingly. The repository ignores `*.csv`, so nobody commits a result by mistake.
