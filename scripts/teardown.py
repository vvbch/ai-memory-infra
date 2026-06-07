#!/usr/bin/env python3
"""Guided, reversible teardown of the ai-memory-infra cloud footprint.

This is the operational expression of the decommission/exit path required by
tenet 12. It tears down everything Terraform created (droplet, firewall,
Cloudflare DNS records, Spaces backups bucket) with a read-the-receipt preview and an
explicit typed confirmation, then prints the short list of things Terraform
*cannot* undo (account billing, the domain registration, the separate state
bucket) so an operator -- or a non-engineer executor following
``docs/decommission.md`` -- can finish the job.

Cross-platform (tenet 3): pure Python 3.12 stdlib, no external deps. Works on
Windows PowerShell and Unix/macOS/WSL the same way.

Usage:
    python scripts/teardown.py --dry-run     # show what WOULD be destroyed, change nothing
    python scripts/teardown.py               # preview, then prompt, then destroy
    python scripts/teardown.py --yes         # destroy without the interactive prompt (CI/scripted)

Exit codes: 0 success, 1 aborted by user, 2 environment/precondition error.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TF_DIR = REPO_ROOT / "infra" / "terraform"


def find_terraform() -> str | None:
    """Locate the terraform binary on PATH, or in the winget install dir."""
    found = shutil.which("terraform")
    if found:
        return found
    # winget installs to a per-user Packages dir and only updates PATH for new
    # shells; fall back to a glob so a fresh install works without a restart.
    local = os.environ.get("LOCALAPPDATA")
    if local:
        pattern = os.path.join(
            local, "Microsoft", "WinGet", "Packages",
            "Hashicorp.Terraform_*", "terraform.exe",
        )
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def run_tf(tf: str, *args: str) -> int:
    """Run a terraform subcommand against infra/terraform, streaming output."""
    cmd = [tf, f"-chdir={TF_DIR}", *args]
    print(f"\n$ {' '.join(cmd)}\n", flush=True)
    return subprocess.call(cmd)


def read_domain() -> str | None:
    """Best-effort: read domain_name from terraform.tfvars for the confirm prompt."""
    tfvars = TF_DIR / "terraform.tfvars"
    if not tfvars.exists():
        return None
    m = re.search(r'^\s*domain_name\s*=\s*"([^"]+)"', tfvars.read_text(), re.MULTILINE)
    return m.group(1) if m else None


MANUAL_CHECKLIST = """
================================================================================
 Terraform has released everything it manages. A few things it CANNOT touch --
 finish these by hand (full plain-English version: docs/decommission.md):
================================================================================

 1. DigitalOcean Spaces STATE bucket (the small terraform-state bucket you made
    by hand in setup Step 6, if you did). Terraform does not own it -- delete it
    in the DO console: Spaces -> select the *-tfstate bucket -> empty -> destroy.

 2. DigitalOcean billing. Destroying resources stops new charges, but the account
    stays open. To fully stop: DO console -> Settings -> Billing, confirm $0 due,
    then close the account if you are decommissioning for good.

 3. The DOMAIN registration (Cloudflare Registrar). Terraform only managed the
    DNS *records*, never the name itself. To stop the yearly renewal: log in at
    dash.cloudflare.com -> Domain Registration -> turn OFF auto-renew.

 4. OpenAI API key + billing. platform.openai.com -> API keys -> revoke the key;
    Billing -> remove the payment method / set a $0 limit.

 5. Local machine hygiene (optional): the daily repo-health scheduled task and
    git hooks are harmless, but to remove them:
       schtasks /Delete /TN "AI-Memory Repo Health" /F
       (and delete .git/hooks/pre-commit in each repo)

 NOTHING in this list is destructive to your data once the droplet is gone.
================================================================================
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Guided teardown of ai-memory-infra cloud infra.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show the destroy plan and exit; change nothing.")
    ap.add_argument("--yes", action="store_true",
                    help="Skip the interactive confirmation (still runs terraform's own apply).")
    args = ap.parse_args()

    tf = find_terraform()
    if not tf:
        print("ERROR: terraform not found on PATH (or winget dir).", file=sys.stderr)
        print("Install it: winget install Hashicorp.Terraform", file=sys.stderr)
        return 2

    state = TF_DIR / "terraform.tfstate"
    has_local_state = state.exists() and state.stat().st_size > 0
    if not has_local_state:
        print("NOTE: no local terraform.tfstate found. If your state lives in DO Spaces")
        print("      (backend.tf uncommented), set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY")
        print("      and run `terraform -chdir=infra/terraform init` first.\n")

    print("=" * 80)
    print(" ai-memory-infra TEARDOWN -- this destroys the droplet, firewall,")
    print(" Cloudflare DNS records, and the Spaces backups bucket that Terraform created.")
    print("=" * 80)

    # 1. Always show the receipt first.
    rc = run_tf(tf, "plan", "-destroy")
    if rc != 0:
        print("\nERROR: `terraform plan -destroy` failed (see above). Aborting.", file=sys.stderr)
        return 2

    if args.dry_run:
        print("\n[--dry-run] Plan shown above. Nothing was changed.")
        return 0

    # 2. Typed confirmation (our gate, on top of terraform's own).
    if not args.yes:
        domain = read_domain()
        token = domain or "destroy"
        print("\n" + "!" * 80)
        print(f" To proceed, type exactly:  {token}")
        print(" (Ctrl-C / anything else aborts. This is billable infra + live DNS.)")
        print("!" * 80)
        try:
            typed = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if typed != token:
            print("Confirmation did not match. Aborted -- nothing destroyed.")
            return 1

    # 3. Destroy. Note: the Spaces backups bucket must be empty for destroy to
    #    succeed; if it has objects, empty it in the DO console and re-run.
    rc = run_tf(tf, "destroy", "-auto-approve")
    if rc != 0:
        print("\nERROR: `terraform destroy` did not complete cleanly (see above).", file=sys.stderr)
        print("Common cause: the Spaces backups bucket is non-empty -- empty it and re-run.",
              file=sys.stderr)
        return 2

    print(MANUAL_CHECKLIST)
    print("Terraform teardown complete. Update docs/planning/STATUS.md, then commit + push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
