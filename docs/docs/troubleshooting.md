# Troubleshooting

Every error below stops the check with exit code 2.

| Message                                                              | Cause and fix                                                                                                                                       |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `401 Unauthorized`                                                   | The token is wrong, expired or revoked. Create a new one.                                                                                           |
| `403 Forbidden`                                                      | The token's user is not an administrator, or Admin Mode is on and the token lacks the `admin_mode` scope.                                           |
| `the URL must start with https://`                                   | The scripts never send the token unencrypted. Use the `https://` address.                                                                           |
| `was redirected (HTTP 301) and the redirect was refused`             | The URL redirects, for example from a short name or a load balancer. Open it in a browser, note the final address, and pass that.                   |
| `GET /license returned HTTP …, so the tier is unknown`               | The licence endpoint failed with something other than "no licence". Without the tier, you can't trust paid-tier results, so the check stops. Retry. |
| `cannot reach …`                                                     | DNS, network, proxy or TLS failure. For an internal CA with Python, add `--ca-bundle`. PowerShell uses the Windows certificate store.               |
| `gave an unreadable response`                                        | Something other than GitLab answered, often a proxy or sign-in page, or the reply was cut off.                                                      |
| `the token contains spaces, line breaks or other invalid characters` | The pasted token has extra characters in it. Paste it again.                                                                                        |

## Settings show as ABSENT

The API on older GitLab versions doesn't return every field in the baseline. Check the setting in the admin area by hand, or remove it from your copy of `baseline.json`.

## PowerShell won't run the script

Windows blocks downloaded scripts under some execution policies. Either unblock the file with `Unblock-File .\Test-GitLabBaseline.ps1`, or run it with `powershell -ExecutionPolicy Bypass -File …`.
