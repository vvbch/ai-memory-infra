<#
.SYNOPSIS
    Install the Tenet 11 / ADR 015 pre-commit integrity hook into each repo.

.DESCRIPTION
    Copies scripts/hooks/pre-commit into <repo>/.git/hooks/pre-commit for every
    repo in the list. A COPY, not a symlink (tenet 3: symlinks are Windows-
    hostile). Because hooks live in .git/ (which is NOT versioned), re-run this
    after any re-clone. The committed shim + this installer are what "survive" a
    re-clone, per ADR 015.

.PARAMETER RepoList
    Repo paths. If omitted, falls back to the AI_MEMORY_REPOS env var
    (paths separated by ';'). If still empty, defaults to THIS repo only.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install-hooks.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install-hooks.ps1 -RepoList "C:\a","C:\b"
#>
[CmdletBinding()]
param([string[]] $RepoList)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$thisRepo = Split-Path -Parent $PSScriptRoot   # scripts/ -> repo root
$shim = Join-Path $PSScriptRoot "hooks\pre-commit"

if (-not (Test-Path -LiteralPath $shim)) {
    Write-Host "ERROR: shim not found at $shim" -ForegroundColor Red
    exit 1
}

# Resolve repo list: param > env var > this repo.
if (-not $RepoList -or $RepoList.Count -eq 0) {
    $envRepos = $env:AI_MEMORY_REPOS
    if (-not [string]::IsNullOrWhiteSpace($envRepos)) {
        $RepoList = $envRepos.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    } else {
        $RepoList = @($thisRepo)
    }
}
$RepoList = $RepoList | ForEach-Object { $_ -split ';' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

$installed = 0
foreach ($repo in $RepoList) {
    $hooksDir = Join-Path $repo ".git\hooks"
    if (-not (Test-Path -LiteralPath $hooksDir)) {
        Write-Host "SKIP (no .git/hooks): $repo" -ForegroundColor Yellow
        continue
    }
    $dest = Join-Path $hooksDir "pre-commit"
    Copy-Item -LiteralPath $shim -Destination $dest -Force
    Write-Host "installed pre-commit -> $dest" -ForegroundColor Green
    $installed++
}

Write-Host ""
Write-Host "Done. Installed into $installed repo(s)." -ForegroundColor Cyan
Write-Host "Re-run this after any re-clone (hooks are not versioned)." -ForegroundColor DarkGray
