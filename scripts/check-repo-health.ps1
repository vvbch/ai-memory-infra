<#
.SYNOPSIS
    Integrity check for git repos that live under Google Drive (Tenet 11 / ADR 015).

.DESCRIPTION
    Google Drive "Mirror" syncs .git internals with no understanding of git
    consistency, which can corrupt a repo: conflicted-copy files inside .git,
    half-synced packs/refs, or a stale index.lock. This script DETECTS those
    states early so the operator can re-clone (not hand-repair). See:
      docs/tenets.md (Tenet 11) · docs/decisions/015-drive-synced-repo-risk.md
      docs/runbook.md ("Drive-sync integrity").

    Per repo it checks:
      1. conflicted-copy files inside .git/        (HARD fail)
      2. stale index.lock                          (HARD fail)
      3. git fsck --full                           (HARD fail; skipped with -Fast)
      4. ahead/behind vs the upstream remote       (INFO; skipped with -Fast)

    Exit codes:  0 = all healthy · 1 = a HARD problem in >=1 repo · 2 = bad args.
    On any HARD problem it writes a timestamped log file and prints its path.

.PARAMETER RepoList
    One or more repo paths. If omitted, falls back to the AI_MEMORY_REPOS env var
    (paths separated by ';'). Never hard-code machine paths in the script.

.PARAMETER Fast
    Pre-commit subset: conflicted-copy + index.lock only (no fsck, no ahead/behind).
    Fast enough to run on every commit.

.PARAMETER LogDir
    Directory for failure logs. Default: <this-repo>/.repo-health-logs (gitignored).

.PARAMETER StaleLockMinutes
    An index.lock older than this many minutes with no active git process is
    treated as stale. Default 5.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\check-repo-health.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\check-repo-health.ps1 -Fast -RepoList "C:\path\to\repo"
#>
[CmdletBinding()]
param(
    [string[]] $RepoList,
    [switch]   $Fast,
    [string]   $LogDir,
    [int]      $StaleLockMinutes = 5
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

# --- Resolve the repo list (param > env var) ------------------------------
if (-not $RepoList -or $RepoList.Count -eq 0) {
    $envRepos = $env:AI_MEMORY_REPOS
    if ([string]::IsNullOrWhiteSpace($envRepos)) {
        Write-Host "ERROR: no repos given. Pass -RepoList or set AI_MEMORY_REPOS (paths separated by ';')." -ForegroundColor Red
        exit 2
    }
    $RepoList = $envRepos.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
}

# Normalize: split any ';'-delimited element (handles `powershell.exe -File`
# flattening `-RepoList "a","b"` into a single string). Windows paths never
# contain ';', so this is safe.
$RepoList = $RepoList | ForEach-Object { $_ -split ';' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

# --- Helpers --------------------------------------------------------------
function Test-GitAvailable {
    $null = Get-Command git -ErrorAction SilentlyContinue
    return $?
}

# Returns a list of problem strings for one repo (empty list = healthy).
function Get-RepoProblems {
    param([string] $RepoPath, [bool] $FastMode, [int] $StaleMinutes)

    $problems = New-Object System.Collections.Generic.List[string]
    $gitDir = Join-Path $RepoPath ".git"

    if (-not (Test-Path -LiteralPath $RepoPath)) {
        $problems.Add("path does not exist: $RepoPath"); return ,$problems
    }
    if (-not (Test-Path -LiteralPath $gitDir)) {
        $problems.Add("not a git repo (no .git): $RepoPath"); return ,$problems
    }

    # 1. Conflicted-copy files inside .git/ (Drive's signature of a bad sync).
    #    Google Drive names conflicts "<name> (<account>'s conflicted copy <date>).<ext>".
    $conflicts = Get-ChildItem -LiteralPath $gitDir -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '(?i)conflicted copy' }
    foreach ($c in $conflicts) {
        $problems.Add("conflicted-copy file in .git: $($c.FullName)")
    }

    # 2. Stale index.lock (abandoned lock blocks all writes).
    $lock = Join-Path $gitDir "index.lock"
    if (Test-Path -LiteralPath $lock) {
        $ageMin = ((Get-Date) - (Get-Item -LiteralPath $lock).LastWriteTime).TotalMinutes
        if ($ageMin -ge $StaleMinutes) {
            $problems.Add(("stale index.lock ({0:N0} min old): {1}" -f $ageMin, $lock))
        } else {
            Write-Host ("    note: fresh index.lock present ({0:N0} min) - a git op may be running" -f $ageMin) -ForegroundColor DarkYellow
        }
    }

    if (-not $FastMode) {
        # 3. git fsck --full
        Push-Location -LiteralPath $RepoPath
        try {
            $fsck = & git fsck --full --strict 2>&1
            $fsckExit = $LASTEXITCODE
            $bad = $fsck | Where-Object { $_ -match '(?i)\b(error|corrupt|missing|bad|dangling commit|broken)\b' -and $_ -notmatch '(?i)^dangling (blob|tree|tag)' }
            if ($fsckExit -ne 0) {
                $problems.Add("git fsck exited $fsckExit")
            }
            foreach ($line in $bad) { $problems.Add("fsck: $line") }

            # 4. ahead/behind vs upstream (info only; no network - uses cached remote ref)
            $upstream = & git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
            if ($LASTEXITCODE -eq 0 -and $upstream) {
                $counts = & git rev-list --left-right --count "$upstream...HEAD" 2>$null
                if ($LASTEXITCODE -eq 0 -and $counts) {
                    $parts = ($counts -split '\s+')
                    $behind = $parts[0]; $ahead = $parts[1]
                    Write-Host "    info: $ahead ahead / $behind behind $upstream" -ForegroundColor DarkCyan
                    if ([int]$ahead -gt 0) {
                        Write-Host "    reminder: un-pushed commits exist - push this session (Tenet 11)." -ForegroundColor Yellow
                    }
                }
            } else {
                Write-Host "    info: no upstream tracking branch set" -ForegroundColor DarkGray
            }
        } finally {
            Pop-Location
        }
    }

    return ,$problems
}

# --- Main -----------------------------------------------------------------
if (-not (Test-GitAvailable)) {
    Write-Host "ERROR: git not found on PATH." -ForegroundColor Red
    exit 2
}

$mode = if ($Fast) { "FAST (pre-commit subset)" } else { "FULL" }
Write-Host "check-repo-health [$mode] - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ("repos: {0}" -f ($RepoList -join ', '))

$allProblems = New-Object System.Collections.Generic.List[string]
foreach ($repo in $RepoList) {
    Write-Host ""
    Write-Host "==> $repo"
    $p = Get-RepoProblems -RepoPath $repo -FastMode:$Fast.IsPresent -StaleMinutes $StaleLockMinutes
    if ($p.Count -eq 0) {
        Write-Host "    OK" -ForegroundColor Green
    } else {
        foreach ($prob in $p) {
            Write-Host "    FAIL: $prob" -ForegroundColor Red
            $allProblems.Add("[$repo] $prob")
        }
    }
}

Write-Host ""
if ($allProblems.Count -eq 0) {
    Write-Host "RESULT: all repos healthy." -ForegroundColor Green
    exit 0
}

# Write a failure log next to the first repo (or the configured LogDir).
if ([string]::IsNullOrWhiteSpace($LogDir)) {
    $LogDir = Join-Path $RepoList[0] ".repo-health-logs"
}
if (-not (Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logFile = Join-Path $LogDir "repo-health-$stamp.log"
$header = @(
    "repo-health FAILURE - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$mode]",
    "ACTION (ADR 015): do NOT hand-repair. Re-clone the affected repo from GitHub",
    "and re-apply uncommitted work. See docs/runbook.md 'Drive-sync integrity'.",
    ""
)
($header + $allProblems) | Set-Content -LiteralPath $logFile -Encoding UTF8

Write-Host "RESULT: $($allProblems.Count) problem(s) found. Log: $logFile" -ForegroundColor Red
Write-Host "ACTION: re-clone from GitHub, do NOT hand-repair (ADR 015)." -ForegroundColor Red
exit 1
