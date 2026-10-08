# What it checks

This page is generated from `baseline.json`, which both scripts read. To change what
counts as a pass, edit `expect` in that file and run `python3 scripts/gen_checks_page.py`.

**Expected** shows the comparison: a plain value must match exactly, `<= n` means the
number must not exceed `n`, and `includes` means the list must contain that value.
**Tier** is the lowest licence tier on which GitLab enforces the setting. **CIS** is the
matching CIS GitLab Benchmark v1.0.1 recommendation, where there is one.

Only change the settings under "Identity after SSO" once single sign-on works, or
administrators can lock themselves out of the web interface.

## Administration

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `admin_mode` | `true` | All tiers | - | Administrators must re-authenticate before using admin rights, and API tokens need the admin_mode scope. |

## Sessions

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `session_expire_delay` | `<= 480` | All tiers | - | Web sessions last at most 8 hours (value in minutes). The default is a week. |
| `session_expire_from_init` | `true` | All tiers | - | The session lifetime counts from sign-in, so activity cannot keep a session alive indefinitely. |
| `remember_me_enabled` | `false` | All tiers | - | Remember me keeps users signed in beyond the session lifetime. |
| `notify_on_unknown_sign_in` | `true` | All tiers | - | Users get an email when someone signs in to their account from an unknown IP address. |

## Sign-up

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `signup_enabled` | `false` | All tiers | - | Anyone who can reach the sign-in page can register an account while this is on. |
| `require_admin_approval_after_user_signup` | `true` | All tiers | - | If someone turns sign-up back on, new accounts still wait for an administrator. |
| `email_confirmation_setting` | `hard` | All tiers | - | Users must confirm their email address before they can sign in. |

## Accounts

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `deactivate_dormant_users` | `true` | All tiers | 1.3.1 | GitLab deactivates accounts that have not been used, so leavers missed by the joiners and leavers process lose access. |
| `deactivate_dormant_users_period` | `<= 90` | All tiers | 1.3.1 | Days of inactivity before deactivation. |

## Creation limits

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `can_create_group` | `false` | All tiers | 1.3.2 | Only administrators create top-level groups, so every group sits under a governed parent. |
| `allow_project_creation_for_guest_and_below` | `false` | All tiers | 1.2.2 | Guests cannot create projects. |
| `default_projects_limit` | `<= 0` | All tiers | 1.2.2 | New users get no personal projects, so code lives in groups the organisation controls. The default is 100,000. |

## Visibility

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `default_project_visibility` | `private` | All tiers | 1.3.8 | New projects start private. |
| `default_group_visibility` | `private` | All tiers | 1.3.8 | New groups start private. |
| `default_snippet_visibility` | `private` | All tiers | 1.3.8 | New snippets start private. |
| `restricted_visibility_levels` | `includes public` | All tiers | 1.3.8 | Only administrators can make a project, group or snippet public. |

## Tokens

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `require_personal_access_token_expiry` | `true` | All tiers | - | Personal, project and group access tokens must have an expiry date. |
| `service_access_tokens_expiration_enforced` | `true` | All tiers | - | Service account tokens must have an expiry date. On Free GitLab always requires one; on Premium and Ultimate this setting decides. |
| `max_personal_access_token_lifetime` | `<= 90` | Ultimate | - | Caps token lifetime in days. Below Ultimate GitLab saves this value but does not enforce it. |

## OAuth applications

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `user_oauth_applications` | `false` | All tiers | 1.4.1 | Users cannot register their own OAuth applications. |
| `disable_admin_oauth_scopes` | `true` | All tiers | 1.4.1 | Administrators cannot authorise untrusted OAuth applications that ask for broad scopes such as full API access or sudo. |

## Outbound requests

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `allow_local_requests_from_web_hooks_and_services` | `false` | All tiers | 1.4.4 | Webhooks and integrations cannot reach the internal network, which limits server-side request forgery. |
| `allow_local_requests_from_system_hooks` | `false` | All tiers | 1.4.4 | System hooks cannot reach the internal network. |
| `dns_rebinding_protection_enabled` | `true` | All tiers | 1.4.4 | Stops a hostname that resolves to a public address at check time from resolving to an internal one at request time. |

## Export

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `silent_admin_exports_enabled` | `false` | All tiers | - | GitLab records exports by administrators in the audit log and notifies project members. |

## Identity after SSO

| Setting | Expected | Tier | CIS | Why |
| ------- | -------- | ---- | --- | --- |
| `password_authentication_enabled_for_web` | `false` | All tiers | 1.3.6 | Users sign in through the organisation's identity provider, not a GitLab password. Only set this once SSO works. |
| `password_authentication_enabled_for_git` | `false` | All tiers | 1.3.6 | Git over HTTPS uses tokens, not the account password. |
| `require_two_factor_authentication` | `true` | All tiers | 1.3.5 | Applies to GitLab password sign-in. Users who sign in through SSO get MFA from the identity provider. |
| `two_factor_grace_period` | `<= 0` | All tiers | 1.3.5 | Hours a user can delay setting up two-factor authentication. |
| `require_admin_two_factor_authentication` | `true` | All tiers | 1.3.5 | Administrators must use two-factor authentication. |
