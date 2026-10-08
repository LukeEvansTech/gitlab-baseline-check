<#
.SYNOPSIS
Read-only check of a GitLab self-managed instance against baseline.json.

.DESCRIPTION
Reads GET /api/v4/application/settings, the licence and the version, then compares each
setting in baseline.json with the instance. It never changes anything on the instance and
prints only the settings it checks. Runs on Windows PowerShell 5.1 and PowerShell 7.

The token comes from the GITLAB_TOKEN environment variable, or a hidden prompt. It needs an
administrator's token with the read_api scope, plus admin_mode when Admin Mode is on.

Exit code 0 means every check passed, 1 means at least one did not, and 2 means the check
could not run.

.PARAMETER Url
Instance URL, for example https://gitlab.example.com.

.PARAMETER CsvPath
Also write the results to this CSV file.

.PARAMETER BaselinePath
Baseline file. Defaults to baseline.json next to this script.

.PARAMETER FromFile
Test mode: read {plan, version, settings} JSON instead of calling an instance.

.EXAMPLE
.\Test-GitLabBaseline.ps1 -Url https://gitlab.example.com -CsvPath results.csv
#>
[CmdletBinding()]
param(
    [string]$Url,
    [string]$CsvPath,
    [string]$BaselinePath = (Join-Path -Path $PSScriptRoot -ChildPath 'baseline.json'),
    [string]$FromFile
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$Rank = @{ free = 0; premium = 1; ultimate = 2 }
# Older licence names map to the tier that replaced them.
$PlanAliases = @{ silver = 'premium'; gold = 'ultimate'; bronze = 'free'; starter = 'free' }
$Columns = @('result', 'area', 'setting', 'expected', 'actual', 'tier', 'cis', 'why')

function Get-Kind {
    param($Value)
    if ($null -eq $Value) { return 'null' }
    if ($Value -is [bool]) { return 'bool' }
    if ($Value -is [string]) { return 'string' }
    if ($Value -is [System.Array]) { return 'list' }
    if ($Value -is [int] -or $Value -is [long] -or $Value -is [decimal] -or $Value -is [double]) { return 'number' }
    return 'other'
}

function Format-Value {
    # Render a value the same way the Python checker does.
    param($Value)
    switch (Get-Kind -Value $Value) {
        'null' { return 'null' }
        'bool' { if ($Value) { return 'true' } else { return 'false' } }
        'list' {
            if ($Value.Count -eq 0) { return '(empty)' }
            return (($Value | ForEach-Object { Format-Value -Value $_ }) -join ';')
        }
        default { return [string]$Value }
    }
}

function Format-Expected {
    param($Check)
    switch ($Check.op) {
        'le' { return '<= ' + (Format-Value -Value $Check.expect) }
        'contains' { return 'includes ' + (Format-Value -Value $Check.expect) }
        default { return Format-Value -Value $Check.expect }
    }
}

function Test-Match {
    param([string]$Op, $Want, $Have)
    switch ($Op) {
        'eq' {
            return ((Get-Kind -Value $Have) -eq (Get-Kind -Value $Want)) -and
                ((Format-Value -Value $Have) -ceq (Format-Value -Value $Want))
        }
        'le' { return ((Get-Kind -Value $Have) -eq 'number') -and ($Have -le $Want) }
        'contains' {
            if ((Get-Kind -Value $Have) -ne 'list') { return $false }
            foreach ($w in @($Want)) { if (@($Have) -cnotcontains $w) { return $false } }
            return $true
        }
        default { throw "unknown op $Op" }
    }
}

function Get-NormalisedPlan {
    param([string]$Plan)
    if (-not $Plan) { $Plan = 'free' }
    $Plan = $Plan.ToLowerInvariant()
    if ($PlanAliases.ContainsKey($Plan)) { $Plan = $PlanAliases[$Plan] }
    if (-not $Rank.ContainsKey($Plan)) { return 'free' }
    return $Plan
}

function Get-Property {
    # Returns @{ Found; Value } so a setting the API omits is told apart from a null one.
    param($Object, [string]$Name)
    $prop = $Object.PSObject.Properties | Where-Object { $_.Name -ceq $Name } | Select-Object -First 1
    if ($null -eq $prop) { return @{ Found = $false; Value = $null } }
    return @{ Found = $true; Value = $prop.Value }
}

function Invoke-GitLabGet {
    # Returns @{ Status; Body }.
    param([string]$Path, [string]$Token)
    $uri = $Url.TrimEnd('/') + '/api/v4' + $Path
    try {
        # MaximumRedirection 0 refuses every redirect, so the token is never sent to another URL.
        $body = Invoke-RestMethod -Uri $uri -Headers @{ 'PRIVATE-TOKEN' = $Token } -Method Get -UseBasicParsing -TimeoutSec 30 -MaximumRedirection 0
    } catch {
        $response = $null
        if ($_.Exception.PSObject.Properties['Response']) { $response = $_.Exception.Response }
        if ($null -eq $response) { throw "cannot reach ${uri}: $($_.Exception.Message)" }
        $status = [int]$response.StatusCode
        if ($status -ge 300 -and $status -lt 400) {
            throw "GET $Path was redirected (HTTP $status) and the redirect was refused. Pass the instance's final https:// URL."
        }
        return @{ Status = $status; Body = $null }
    }
    # Windows PowerShell 5.1 returns a JSON null body as the string 'null'.
    if ($body -is [string] -and $body.Trim() -eq 'null') { $body = $null }
    # A proxy can answer 200 with an HTML page; Invoke-RestMethod then returns a string.
    if ($null -ne $body -and $body -isnot [System.Management.Automation.PSCustomObject]) {
        throw "GET $Path gave an unreadable response (not JSON)."
    }
    return @{ Status = 200; Body = $body }
}

function Get-InstanceState {
    param([string]$Token)
    $r = Invoke-GitLabGet -Path '/application/settings' -Token $Token
    if ($r.Status -eq 401) { throw '401 Unauthorized: the token is invalid, expired or revoked.' }
    if ($r.Status -eq 403) {
        throw '403 Forbidden: the token must belong to an administrator. If Admin Mode is on, the token also needs the admin_mode scope.'
    }
    if ($r.Status -ne 200 -or $null -eq $r.Body) { throw "GET /application/settings returned HTTP $($r.Status)." }
    $settings = $r.Body

    $meta = Invoke-GitLabGet -Path '/metadata' -Token $Token
    if ($meta.Status -ne 200 -or $null -eq $meta.Body) { $meta = Invoke-GitLabGet -Path '/version' -Token $Token }
    $version = 'unknown'
    $enterprise = $null
    if ($null -ne $meta.Body) {
        $v = Get-Property -Object $meta.Body -Name 'version'
        if ($v.Found) { $version = [string]$v.Value }
        $e = Get-Property -Object $meta.Body -Name 'enterprise'
        if ($e.Found) { $enterprise = $e.Value }
    }

    $lic = Invoke-GitLabGet -Path '/license' -Token $Token
    # Community Edition has no licence endpoint (404); Enterprise without a licence returns
    # null. Any other failure leaves the tier unknown, so stop.
    if ($enterprise -eq $false -or $lic.Status -eq 404 -or ($lic.Status -eq 200 -and $null -eq $lic.Body)) {
        $plan = 'free'
    } elseif ($lic.Status -eq 200) {
        # An expired trial turns paid features off and an expired paid licence does not, but
        # the licence API does not say which one it is. Treat any expired licence as Free, so
        # a paid-tier setting can show NOT ENFORCED wrongly but never PASS wrongly.
        $plan = Get-NormalisedPlan -Plan ([string](Get-Property -Object $lic.Body -Name 'plan').Value)
        if ([bool](Get-Property -Object $lic.Body -Name 'expired').Value) {
            [Console]::Error.WriteLine("warning: the $plan licence has expired, so paid-tier settings are checked as Free. If it was a paid licence, not a trial, they may still apply.")
            $plan = 'free'
        }
    } else {
        throw "GET /license returned HTTP $($lic.Status), so the tier is unknown."
    }
    return @{ Settings = $settings; Plan = $plan; Version = $version }
}

function Get-Result {
    param($Checks, $Settings, [string]$Plan)
    foreach ($check in $Checks) {
        $have = Get-Property -Object $Settings -Name $check.setting
        if (-not $have.Found) {
            $result = 'ABSENT'
            $actual = '(absent)'
        } else {
            $actual = Format-Value -Value $have.Value
            if (-not (Test-Match -Op $check.op -Want $check.expect -Have $have.Value)) {
                $result = 'FAIL'
            } elseif ($Rank[$Plan] -lt $Rank[$check.tier]) {
                $result = 'NOT ENFORCED'
            } else {
                $result = 'PASS'
            }
        }
        [pscustomobject]@{
            result   = $result
            area     = $check.area
            setting  = $check.setting
            expected = Format-Expected -Check $check
            actual   = $actual
            tier     = $check.tier
            cis      = $check.cis
            why      = $check.why
        }
    }
}

function ConvertTo-CsvField {
    param([string]$Value)
    if ($Value -match '[",\r\n]') { return '"' + $Value.Replace('"', '""') + '"' }
    return $Value
}

function Write-ResultCsv {
    # Minimal quoting, UTF-8 without BOM and LF line ends, to match the Python checker byte for byte.
    param($Rows, [string]$Path)
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add($Columns -join ',')
    foreach ($row in $Rows) {
        $lines.Add((($Columns | ForEach-Object { ConvertTo-CsvField -Value $row.$_ }) -join ','))
    }
    $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    [System.IO.File]::WriteAllText($full, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding $false))
}

try {
    $checks = (Get-Content -Path $BaselinePath -Raw | ConvertFrom-Json).checks
    if ($FromFile) {
        $data = Get-Content -Path $FromFile -Raw | ConvertFrom-Json
        $state = @{ Settings = $data.settings; Plan = (Get-NormalisedPlan -Plan $data.plan); Version = $data.version }
    } else {
        if (-not $Url) { throw '-Url is required' }
        if (-not $Url.StartsWith('https://', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'the URL must start with https://, so the token is encrypted.'
        }
        # Windows PowerShell 5.1 may not offer TLS 1.2 by default.
        if ($PSVersionTable.PSVersion.Major -lt 6) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        }
        $token = $env:GITLAB_TOKEN
        if (-not $token) {
            $secure = Read-Host -Prompt 'GitLab token' -AsSecureString
            $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
        }
        $token = $token.Trim()
        # Header errors can quote the value, so reject a malformed token before any request.
        if ($token -cnotmatch '^[\x21-\x7e]+$') {
            throw 'the token contains spaces, line breaks or other invalid characters.'
        }
        $state = Get-InstanceState -Token $token
    }

    $rows = @(Get-Result -Checks $checks -Settings $state.Settings -Plan $state.Plan)
    $plan = $state.Plan

    Write-Output "GitLab $($state.Version), licence tier: $plan`n"
    $width = ($rows | ForEach-Object { $_.setting.Length } | Measure-Object -Maximum).Maximum
    Write-Output ("{0,-13} {1,-$width} {2,18} {3,18}" -f 'RESULT', 'SETTING', 'EXPECTED', 'ACTUAL')
    foreach ($r in $rows) {
        Write-Output ("{0,-13} {1,-$width} {2,18} {3,18}" -f $r.result, $r.setting, $r.expected, $r.actual)
    }
    $count = @{}
    foreach ($k in 'PASS', 'FAIL', 'NOT ENFORCED', 'ABSENT') { $count[$k] = @($rows | Where-Object { $_.result -eq $k }).Count }
    Write-Output ("`n{0} of {1} pass, {2} fail, {3} set but not enforced on {4}, {5} absent" -f
        $count['PASS'], $rows.Count, $count['FAIL'], $count['NOT ENFORCED'], $plan, $count['ABSENT'])

    if ($CsvPath) {
        Write-ResultCsv -Rows $rows -Path $CsvPath
        Write-Output "wrote $CsvPath"
    }
} catch {
    [Console]::Error.WriteLine("error: $($_.Exception.Message)")
    exit 2
}

if ($count['PASS'] -eq $rows.Count) { exit 0 } else { exit 1 }
