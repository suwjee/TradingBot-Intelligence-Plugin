"""Install a local Git post-commit hook without replacing an existing hook."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def install(project: Path, vault: Path) -> Path:
    project = project.resolve()
    vault = vault.resolve()
    script = Path(__file__).resolve().parent / "sync_sources.py"
    result = subprocess.run(["git", "-C", str(project), "rev-parse", "--git-path", "hooks/post-commit"],
                            capture_output=True, text=True, check=True)
    hook = Path(result.stdout.strip())
    if not hook.is_absolute():
        hook = project / hook
    hook = hook.resolve()
    if hook.exists():
        raise RuntimeError(f"Existing post-commit hook preserved: {hook}")
    hook.parent.mkdir(parents=True, exist_ok=True)
    exe = sys.executable.replace("\\", "/")
    script_arg = str(script).replace("\\", "/")
    project_arg = str(project).replace("\\", "/")
    vault_arg = str(vault).replace("\\", "/")
    content = ("#!/bin/sh\n"
               f'"{exe}" -B "{script_arg}" --project "{project_arg}" '
               f'--vault "{vault_arg}"\n')
    hook.write_text(content, encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    return hook


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(install(args.project, args.vault))
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
