<#
.SYNOPSIS
    Install the pre-commit guard (repo-integrity + secret-scan) into each repo.

.DESCRIPTION
    Copies scripts/hooks/pre-commit into <repo>/.git/hooks/pre-commit for every
    repo in the list. A COPY, not a symlink (tenet 3: symlinks are Windows-
    hostile). Because hooks live in .git/ (which is NOT versioned), re-run this
    after any re-clone. The committed shim + this installer are what "survive" a
    re-clone, per ADR 015.

    The shim runs TWO gates, both of which BLOCK the commit on failure:
      1. repo-integrity (Tenet 11 / ADR 015) — Drive-sync corruption check.
      2. secret-scan (Tenet 14 / AGENTS.md secrets rule) — gitleaks on staged
         changes ("no secrets in git" as a deterministic gate).
    Gate 2 needs the `gitleaks` binary on PATH, so this installer also ENSURES
    gitleaks is present (auto-installs via winget on Windows when missing).

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

# --- Ensure gitleaks (secret-scan gate, Tenet 14) ---------------------------
# The pre-commit shim BLOCKS commits if gitleaks is missing, so the gate is only
# deterministic when the binary is present. Check PATH; auto-install via winget
# on Windows when missing. Refresh PATH in-process so the check sees a just-
# installed binary without a shell restart.
Write-Host ""
Write-Host "Checking secret-scan dependency (gitleaks)..." -ForegroundColor Cyan
function Test-Gitleaks { [bool](Get-Command gitleaks -ErrorAction SilentlyContinue) }

if (-not (Test-Gitleaks)) {
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path','User')
}

if (Test-Gitleaks) {
    Write-Host "gitleaks present: $((Get-Command gitleaks).Source)" -ForegroundColor Green
} elseif (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "gitleaks missing -> installing via winget (Gitleaks.Gitleaks)..." -ForegroundColor Yellow
    winget install --id Gitleaks.Gitleaks -e `
        --accept-source-agreements --accept-package-agreements --disable-interactivity
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path','User')
    if (Test-Gitleaks) {
        Write-Host "gitleaks installed: $((Get-Command gitleaks).Source)" -ForegroundColor Green
        Write-Host "NOTE: open a NEW shell / restart your editor so gitleaks is on PATH for commits." -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: gitleaks still not on PATH. Open a new shell, or install manually:" -ForegroundColor Red
        Write-Host "  winget install Gitleaks.Gitleaks" -ForegroundColor Red
    }
} else {
    Write-Host "WARNING: gitleaks missing and winget unavailable. Install gitleaks manually:" -ForegroundColor Red
    Write-Host "  https://github.com/gitleaks/gitleaks/releases  (add to PATH)" -ForegroundColor Red
    Write-Host "Until then, commits will be BLOCKED by the secret-scan gate (Tenet 14)." -ForegroundColor Red
}
