# Skill: Operator Assistant — credential handoff (clipboard → agent)

> Fourth Operator Assistant mechanism (2026-06-10). Complements
> `operator_action.py`: that skill formats steps the operator must do in a
> browser/console; **this** skill covers secrets the operator copies once and
> the agent consumes via a script — zero shell commands for the operator.

**Implementation:** `scripts/ssh_unlock.py` (SSH passphrase today; same pattern
for future paste-handoff scripts)
**Owner persona:** Operator Assistant
**Related:** `docs/coe/2026-06-09-concierge-handoff-regression.md` (vague
delegation); AGENTS.md pre-delegation gate

## What pain it removes

The agent asked the operator to run `ssh-add` and paste a passphrase in PowerShell —
mechanical work the agent can do once the value is on the clipboard. That wastes
operator attention and violates the spirit of the pre-delegation gate ("if the
agent can run the CLI equivalent, it should").

## Routine (SSH unlock)

| Who | Does what |
|---|---|
| **Operator** | Copy the SSH key passphrase from the password manager to the system clipboard (one copy). Say **"copied"**, **"in clipboard"**, or **"key is copied to clipboard"**. |
| **Agent** | Run `python scripts/ssh_unlock.py` from `ai-memory-infra`. Never echo clipboard contents. Report only the script's safe status lines. Continue droplet work if probe passes. |

The script:

1. **Probes SSH first** — if the droplet already answers, skips `ssh-add` (idempotent).
2. Reads the clipboard (platform-specific; Windows `Get-Clipboard`).
3. Ensures `ssh-agent` is running (starts the Windows service if needed).
4. Runs `ssh-add` on `~/.ssh/id_ed25519` (or `id_rsa`). Windows OpenSSH cannot
   take a piped passphrase; the script uses `SSH_ASKPASS` + `CreateNoWindow`.
5. **Clears the clipboard** after success.
6. Probes `ssh -o BatchMode=yes root@168.144.145.29 echo ok` by default.

## Store / retrieve boundary

| | |
|---|---|
| **May write** | "SSH unlocked", probe result, key filename (not path secrets) |
| **Must never write** | Passphrase, clipboard contents, `ssh-add` stdin, or any copied vault value |
| **Canonical truth** | AGENTS.md § credential handoff; droplet host in `STATUS.md` Environment notes |

## Success condition

`python scripts/ssh_unlock.py --json` returns `"ok": true` and `"probe_ok": true`
(or operator confirms droplet command works). `--check` returns ok when clipboard
is non-empty before unlock.

## Persist, don't repeat (2026-06-10)

A clipboard handoff is a **first-time or recovery** path, never a routine. If the
same secret would be handed off in a second session, the agent must make it
durable on the machine in the same session instead (AGENTS.md § persistent agent
credentials): OS-native store (ssh-agent service on Automatic, GCM, `gh`
keyring) → Windows user env var → gitignored local file — then verify with a
non-interactive probe. SSH is the worked example: after the service was set to
Automatic and the key registered, `ssh -o BatchMode=yes` succeeds with no
handoff; `ssh_unlock.py` is now fallback-only.

## When to use vs `operator_action.py`

| Situation | Use |
|---|---|
| Operator must click/consent in a web UI | `operator_action.py` |
| Operator must copy a secret; agent can run the consuming command | **this skill** (`ssh_unlock.py`, future handoff scripts) |
| No secret involved; agent can run everything | Neither — just run it |

## Usage

```bash
# After operator says passphrase is on clipboard:
python scripts/ssh_unlock.py

# Pre-flight (clipboard non-empty, no unlock):
python scripts/ssh_unlock.py --check

# Machine-readable:
python scripts/ssh_unlock.py --json
```
