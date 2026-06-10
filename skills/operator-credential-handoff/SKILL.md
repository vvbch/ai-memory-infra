---
name: operator-credential-handoff
description: Use when Chandra copies a secret to the clipboard (SSH passphrase, token) and says "copied" / "in clipboard" / "key is copied" — run scripts/ssh_unlock.py (or future handoff scripts); never ask him to run unlock commands himself.
---

# Operator Credential Handoff (clipboard → agent)

Canonical spec: `ai-memory-infra/docs/skills/operator-assistant-credential-handoff.md`
(governs). Concierge rules: `ai-memory-infra/AGENTS.md` § credential handoff.

## Trigger phrases

- "key is copied (to clipboard)"
- "passphrase is in clipboard" / "copied"
- "SSH unlock" after a prior "copy passphrase" instruction
- Any droplet/SSH block where STATUS says ssh-agent is operator-gated

## Agent routine (SSH)

1. **Do not** delegate `ssh-add`, PowerShell, or terminal paste commands to Chandra.
2. If clipboard may be empty, ask for **one** operator step only: copy the SSH key
   passphrase from Bitwarden → clipboard → say "copied".
3. Run from `ai-memory-infra`:

   `python scripts/ssh_unlock.py`

4. Report only safe script output (never echo clipboard/passphrase).
5. On `probe_ok`, continue the blocked work (e.g. droplet deploy). On fail, one
   concise diagnosis — do not print a resume prompt mid-flow.

## Rules

- **Pre-delegation gate still applies:** copy-to-clipboard is operator-exclusive;
  everything after "copied" is agent-owned.
- **Never log secrets** — not in chat, not in STATUS, not in commit messages.
- For non-SSH paste handoffs, add a dedicated script before improvising shell.
