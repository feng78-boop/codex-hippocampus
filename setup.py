#!/usr/bin/env python3
"""Hippocampus interactive setup — choose global or project-local memory."""

import os
import sys
from pathlib import Path

BANNER = r"""
 ╔══════════════════════════════════════╗
 ║    🧠  Hippocampus  Memory Setup     ║
 ╚══════════════════════════════════════╝
"""

SCOPE_HELP = """
Choose your memory scope:

  [G] Global  (default) — one brain across all projects
      Data: ~/.codex/hippocampus/global/

  [L] Local   — memory stays inside this project only
      Data: ./.hippocampus/

  Tip: You can always override with:
       $env:HIPPOCAMPUS_SCOPE = "local"   (PowerShell)
       export HIPPOCAMPUS_SCOPE=local     (Bash)
"""

def main():
    print(BANNER)
    print(SCOPE_HELP)

    choice = input("Scope [G/l]: ").strip().lower()
    scope = "local" if choice == "l" else "global"

    data_dir = os.path.join(os.getcwd(), ".hippocampus") if scope == "local" \
        else os.path.join(os.path.expanduser("~"), ".codex", "hippocampus", "global")

    Path(data_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n✓ Scope set to: {scope}")
    print(f"  Data directory: {data_dir}")

    if scope == "local":
        print(f"\n  To activate, set the environment variable in your shell:")
        print(f"    PowerShell:  $env:HIPPOCAMPUS_SCOPE = \"local\"")
        print(f"    Bash:        export HIPPOCAMPUS_SCOPE=local")
        print(f"\n  Or create a .hippocampus marker file (engine auto-detects it).")
        Path(os.path.join(os.getcwd(), ".hippocampus")).mkdir(parents=True, exist_ok=True)
    else:
        print(f"\n  Global mode is the default — no environment variable needed.")
        print(f"  Just run: python -m hippocampus.engine stats")

    print(f"\n  Happy remembering! 🧠\n")

if __name__ == "__main__":
    main()
