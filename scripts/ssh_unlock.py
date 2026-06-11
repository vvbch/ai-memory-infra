#!/usr/bin/env python3
"""Load the operator's SSH key into ssh-agent from the system clipboard.

WHY THIS EXISTS
---------------
Droplet work is blocked until ssh-agent holds the decrypted key. The passphrase
lives in password manager — operator-exclusive — but the *unlock command* is not: once
the passphrase is on the clipboard, the agent can run ssh-add without asking
the operator to type shell commands (credential handoff skill; AGENTS.md).

SECURITY
--------
* Never prints clipboard contents, passphrases, or ssh-add stdin.
* Clears the clipboard after a successful load (default) so the passphrase does
  not linger.
* Probe uses ``ssh -o BatchMode=yes`` only — no interactive prompts.

USAGE
-----
  # Operator copies passphrase to clipboard, then says "copied":
  python scripts/ssh_unlock.py

  # Validate clipboard is non-empty without unlocking:
  python scripts/ssh_unlock.py --check

  # Machine-readable:
  python scripts/ssh_unlock.py --json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROBE_HOST = "root@168.144.145.29"
DEFAULT_KEY_CANDIDATES = (
    Path.home() / ".ssh" / "id_ed25519",
    Path.home() / ".ssh" / "id_rsa",
)


@dataclass(frozen=True)
class UnlockResult:
    ok: bool
    clipboard_ready: bool
    agent_running: bool
    key_loaded: bool
    probe_ok: bool | None
    key_path: str | None
    messages: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "clipboard_ready": self.clipboard_ready,
            "agent_running": self.agent_running,
            "key_loaded": self.key_loaded,
            "probe_ok": self.probe_ok,
            "key_path": self.key_path,
            "messages": self.messages,
        }


def _read_clipboard() -> str:
    system = platform.system()
    if system == "Windows":
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError("could not read clipboard (PowerShell Get-Clipboard failed)")
        return proc.stdout
    if system == "Darwin":
        proc = subprocess.run(["pbpaste"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError("could not read clipboard (pbpaste failed)")
        return proc.stdout
    for cmd in (["wl-paste", "-n"], ["xclip", "-o", "-selection", "clipboard"]):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            continue
        if proc.returncode == 0:
            return proc.stdout
    raise RuntimeError("no clipboard reader found on this platform")


def _clear_clipboard() -> None:
    system = platform.system()
    if system == "Windows":
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $null"],
            capture_output=True,
            check=False,
        )
        return
    if system == "Darwin":
        subprocess.run(["pbcopy"], input="", text=True, check=False)
        return
    for cmd in (
        ["wl-copy", ""],
        ["xclip", "-selection", "clipboard", "/dev/null"],
    ):
        try:
            subprocess.run(cmd, capture_output=True, check=False)
            return
        except FileNotFoundError:
            continue


def _ensure_ssh_agent(messages: list[str]) -> bool:
    if platform.system() != "Windows":
        if os.environ.get("SSH_AUTH_SOCK"):
            return True
        messages.append("SSH_AUTH_SOCK is unset; start ssh-agent in this shell first")
        return False

    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$s = Get-Service ssh-agent -ErrorAction SilentlyContinue; "
                "if (-not $s) { exit 2 }; "
                "if ($s.Status -ne 'Running') { Start-Service ssh-agent }; "
                "if ((Get-Service ssh-agent).Status -eq 'Running') { exit 0 } else { exit 1 }"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 2:
        messages.append("ssh-agent service is not installed on Windows OpenSSH")
        return False
    if proc.returncode != 0:
        messages.append("could not start ssh-agent service")
        return False
    messages.append("ssh-agent is running")
    return True


def _resolve_key_path(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    for candidate in DEFAULT_KEY_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def _ssh_add_windows_askpass(key_path: Path, passphrase: str) -> subprocess.CompletedProcess[str]:
    """Windows OpenSSH: SSH_ASKPASS + CreateNoWindow (stdin pipe does not work)."""
    askpass = Path(tempfile.gettempdir()) / f"ai-memory-askpass-{os.getpid()}.cmd"
    ps1 = Path(tempfile.gettempdir()) / f"ai-memory-ssh-add-{os.getpid()}.ps1"
    try:
        askpass.write_text("@echo off\r\necho %SSH_UNLOCK_PASS%\r\n", encoding="ascii")
        ps1.write_text(
            "\n".join(
                [
                    "$ErrorActionPreference = 'Stop'",
                    "$s = Get-Service ssh-agent -ErrorAction SilentlyContinue",
                    "if ($s -and $s.Status -ne 'Running') { Start-Service ssh-agent }",
                    f"$key = '{key_path}'",
                    f"$ask = '{askpass}'",
                    "$env:SSH_UNLOCK_PASS = $env:AI_MEMORY_SSH_UNLOCK_PASS",
                    "$env:SSH_ASKPASS = $ask",
                    "$env:SSH_ASKPASS_REQUIRE = 'force'",
                    "$env:DISPLAY = 'dummy'",
                    "$psi = New-Object System.Diagnostics.ProcessStartInfo",
                    "$psi.FileName = 'ssh-add'",
                    "$psi.Arguments = $key",
                    "$psi.UseShellExecute = $false",
                    "$psi.CreateNoWindow = $true",
                    "$psi.RedirectStandardOutput = $true",
                    "$psi.RedirectStandardError = $true",
                    "$proc = [System.Diagnostics.Process]::Start($psi)",
                    "if (-not $proc.WaitForExit(25000)) { $proc.Kill(); exit 124 }",
                    "if ($proc.ExitCode -ne 0) {",
                    "  Write-Error ($proc.StandardError.ReadToEnd())",
                    "}",
                    "exit $proc.ExitCode",
                ]
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["AI_MEMORY_SSH_UNLOCK_PASS"] = passphrase
        return subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            capture_output=True,
            text=True,
            check=False,
            timeout=35,
            env=env,
        )
    finally:
        for path in (askpass, ps1):
            with contextlib.suppress(OSError):
                path.unlink()


def _write_askpass_helper(env: dict[str, str], passphrase: str) -> Path:
    """Return a temp askpass script; sets SSH_ASKPASS* env vars (caller deletes file)."""
    token = "SSH_UNLOCK_ASKPASS"
    env[token] = passphrase
    script = Path(tempfile.gettempdir()) / f"ai-memory-askpass-{os.getpid()}.py"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f"sys.stdout.write(os.environ[{token!r}])\n",
        encoding="utf-8",
    )
    script.chmod(0o700)
    env["SSH_ASKPASS"] = str(script)
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = env.get("DISPLAY", ":0")
    return script


def _ssh_add(key_path: Path, passphrase: str) -> bool:
    try:
        if platform.system() == "Windows":
            proc = _ssh_add_windows_askpass(key_path, passphrase)
        else:
            env = os.environ.copy()
            askpass: Path | None = None
            token = "SSH_UNLOCK_ASKPASS"
            try:
                askpass = _write_askpass_helper(env, passphrase)
                proc = subprocess.run(
                    ["ssh-add", str(key_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    env=env,
                    timeout=30,
                )
            finally:
                env.pop(token, None)
                if askpass is not None:
                    with contextlib.suppress(OSError):
                        askpass.unlink()
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ssh-add timed out (bad passphrase or agent unavailable)") from exc

    if proc.returncode == 124:
        raise RuntimeError("ssh-add timed out (bad passphrase or agent unavailable)")
    if proc.returncode == 2:
        raise RuntimeError("clipboard is empty")
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if err:
            raise RuntimeError(err.splitlines()[-1][:200])
        raise RuntimeError("ssh-add failed")
    return True


def _probe_ssh(host: str) -> bool:
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=15",
                "-o",
                "StrictHostKeyChecking=accept-new",
                host,
                "echo",
                "ok",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=25,
        )
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0 and "ok" in proc.stdout


def _clipboard_ready(passphrase: str) -> bool:
    text = passphrase.strip()
    return 2 <= len(text) <= 512


def unlock(
    *,
    key_path: str | None = None,
    probe_host: str | None = None,
    clear_clipboard: bool = True,
    dry_run: bool = False,
) -> UnlockResult:
    messages: list[str] = []
    probe_ok: bool | None = None
    resolved = _resolve_key_path(key_path)
    if resolved is None:
        return UnlockResult(
            ok=False,
            clipboard_ready=False,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=None,
            messages=["no SSH private key found (~/.ssh/id_ed25519 or id_rsa)"],
        )

    try:
        passphrase = _read_clipboard()
    except RuntimeError as exc:
        return UnlockResult(
            ok=False,
            clipboard_ready=False,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=str(resolved),
            messages=[str(exc)],
        )

    if not _clipboard_ready(passphrase):
        return UnlockResult(
            ok=False,
            clipboard_ready=False,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=str(resolved),
            messages=["clipboard is empty or does not look like a passphrase — copy it first"],
        )

    if dry_run:
        return UnlockResult(
            ok=True,
            clipboard_ready=True,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=str(resolved),
            messages=["clipboard ready (dry-run / --check only)"],
        )

    if probe_host and _probe_ssh(probe_host):
        messages.append(f"SSH probe already ok ({probe_host}); skipped ssh-add")
        if clear_clipboard:
            _clear_clipboard()
            messages.append("clipboard cleared")
        return UnlockResult(
            ok=True,
            clipboard_ready=True,
            agent_running=True,
            key_loaded=True,
            probe_ok=True,
            key_path=str(resolved),
            messages=messages,
        )

    if not _ensure_ssh_agent(messages):
        return UnlockResult(
            ok=False,
            clipboard_ready=True,
            agent_running=False,
            key_loaded=False,
            probe_ok=None,
            key_path=str(resolved),
            messages=messages,
        )

    try:
        _ssh_add(resolved, passphrase.rstrip("\r\n"))
    except RuntimeError as exc:
        return UnlockResult(
            ok=False,
            clipboard_ready=True,
            agent_running=True,
            key_loaded=False,
            probe_ok=None,
            key_path=str(resolved),
            messages=[f"ssh-add failed: {exc}"],
        )

    messages.append(f"loaded key {resolved.name}")
    if clear_clipboard:
        _clear_clipboard()
        messages.append("clipboard cleared")

    if probe_host:
        probe_ok = _probe_ssh(probe_host)
        if probe_ok:
            messages.append(f"SSH probe ok ({probe_host})")
        else:
            messages.append(f"SSH probe failed ({probe_host})")
            return UnlockResult(
                ok=False,
                clipboard_ready=True,
                agent_running=True,
                key_loaded=True,
                probe_ok=False,
                key_path=str(resolved),
                messages=messages,
            )

    return UnlockResult(
        ok=True,
        clipboard_ready=True,
        agent_running=True,
        key_loaded=True,
        probe_ok=probe_ok,
        key_path=str(resolved),
        messages=messages,
    )


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ssh_unlock",
        description="Load SSH key into ssh-agent from clipboard (never prints secrets).",
    )
    p.add_argument("--key-path", default="", help="private key file (default: ~/.ssh/id_ed25519)")
    p.add_argument(
        "--probe-host",
        default=DEFAULT_PROBE_HOST,
        help=f"ssh BatchMode probe after unlock (default: {DEFAULT_PROBE_HOST})",
    )
    p.add_argument("--no-probe", action="store_true", help="skip SSH probe after unlock")
    p.add_argument(
        "--no-clear-clipboard",
        action="store_true",
        help="do not clear clipboard after successful ssh-add",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="only verify clipboard looks ready; do not unlock",
    )
    p.add_argument("--json", action="store_true", help="machine-readable output")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

    args = _parse(argv)
    result = unlock(
        key_path=args.key_path or None,
        probe_host=None if args.no_probe else args.probe_host,
        clear_clipboard=not args.no_clear_clipboard,
        dry_run=args.check,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1

    if result.ok:
        print("ssh-unlock: OK")
        for msg in result.messages:
            print(f"  - {msg}")
        return 0

    print("ssh-unlock: FAIL")
    for msg in result.messages:
        print(f"  - {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
