<#
.SYNOPSIS
    Register (or remove) a daily Windows Scheduled Task that runs the FULL
    repo-health check unattended (Tenet 11 / ADR 015, scheduled layer).

.DESCRIPTION
    Creates a per-user Scheduled Task that runs scripts/check-repo-health.ps1
    daily at -Time against -RepoList. Runs with S4U logon (no stored password,
    fires even when the user is locked/not interactively logged in; the full
    check needs no network). Failures are written by the check script to -LogDir
    AND recorded as a non-zero "Last Run Result" in Task Scheduler history.

    No admin rights needed for a per-user task. Re-run with -Unregister to remove.

.PARAMETER RepoList
    Repo paths. Falls back to AI_MEMORY_REPOS (';'-separated), else this repo.
.PARAMETER Time
    Daily start time, HH:mm. Default 09:00.
.PARAMETER TaskName
    Scheduled task name. Default "AI-Memory Repo Health".
.PARAMETER LogDir
    Where the check writes failure logs. Default %LOCALAPPDATA%\ai-memory-repo-health\logs
    (outside the Drive repo, so logs aren't themselves Drive-synced).
.PARAMETER Unregister
    Remove the task instead of creating it.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\register-repo-health-task.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\register-repo-health-task.ps1 -Unregister
#>
[CmdletBinding()]
param(
    [string[]] $RepoList,
    [string]   $Time = "09:00",
    [string]   $TaskName = "AI-Memory Repo Health",
    [string]   $LogDir,
    [switch]   $Unregister
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if ($Unregister) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'." -ForegroundColor Green
    } else {
        Write-Host "No task named '$TaskName' found." -ForegroundColor Yellow
    }
    exit 0
}

$thisRepo  = Split-Path -Parent $PSScriptRoot
$checkPath = Join-Path $PSScriptRoot "check-repo-health.ps1"
if (-not (Test-Path -LiteralPath $checkPath)) {
    Write-Host "ERROR: $checkPath not found." -ForegroundColor Red; exit 1
}

# Resolve repo list: param > env > this repo.
if (-not $RepoList -or $RepoList.Count -eq 0) {
    $envRepos = $env:AI_MEMORY_REPOS
    if (-not [string]::IsNullOrWhiteSpace($envRepos)) {
        $RepoList = $envRepos.Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    } else {
        $RepoList = @($thisRepo)
    }
}
$RepoList = $RepoList | ForEach-Object { $_ -split ';' } | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

if ([string]::IsNullOrWhiteSpace($LogDir)) {
    $LogDir = Join-Path $env:LOCALAPPDATA "ai-memory-repo-health\logs"
}

# Pass the repo list as ONE ';'-joined quoted arg. `powershell.exe -File` would
# flatten a comma-array into a single token anyway; the check script splits ';'.
$repoJoined = $RepoList -join ';'
$argStr = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -RepoList "{1}" -LogDir "{2}"' -f $checkPath, $repoJoined, $LogDir

$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argStr
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
# Interactive logon: registers WITHOUT admin and runs at the scheduled time while
# the user is logged on (the normal case for a dev box). For run-when-logged-off
# (S4U/batch) you must register from an elevated shell; not needed here.
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings `
        -Description "Daily Tenet 11 / ADR 015 integrity check for Drive-synced repos. Failure log: $LogDir" `
        -ErrorAction Stop | Out-Null
} catch {
    Write-Host "ERROR: could not register task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "If 'Access is denied', re-run this script once from an elevated PowerShell" -ForegroundColor Yellow
    Write-Host "(Run as Administrator). The soft + pre-commit layers still protect you meanwhile." -ForegroundColor Yellow
    exit 1
}

Write-Host "Registered '$TaskName' - daily at $Time." -ForegroundColor Green
Write-Host "  repos:   $($RepoList -join ', ')"
Write-Host "  log dir: $LogDir"
$info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
if ($info -and $info.NextRunTime) { Write-Host "  next run: $($info.NextRunTime)" }
Write-Host "Run now to test:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor DarkGray
