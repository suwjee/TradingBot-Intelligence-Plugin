"""Capture only clean, committed-tracked TradingBot source into the Vault.

The post-commit hook runs this locally. It skips dirty paths, preserves exact
working-tree bytes for clean tracked files, and never publishes to GitHub.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrity import strict_json_loads

def git(project: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(project), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frontmatter(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8-sig")
    head, body = raw[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        key, value = line.split(": ", 1)
        if key in fields:
            raise ValueError(f"Duplicate frontmatter field: {key}")
        fields[key] = strict_json_loads(value)
    return fields, body


def reference_metadata(content: bytes) -> dict:
    """Read declared document identity without inferring trading semantics."""
    text = content.decode("utf-8-sig")
    fields = {"line_count": len(text.splitlines())}
    for key, label in (("version", "Document Version"), ("direction", "Target Direction")):
        match = re.search(r"^\*\*" + label + r":\*\* `([^`]+)`", text, re.MULTILINE)
        if match:
            fields[key] = match.group(1)
    return fields


def write_note(path: Path, fields: dict, body: str) -> None:
    header = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                       for key, value in fields.items())
    path.write_text(f"---\n{header}\n---\n{body}", encoding="utf-8")


def sync(project: Path, vault: Path, check: bool = False) -> dict:
    project = project.resolve()
    vault = vault.resolve()
    if not check:
        builder = vault / "_SCHEMA/build_indexes.py"
        if not builder.is_file():
            raise RuntimeError("Vault index builder is missing")
        dependency = subprocess.run([sys.executable, "-B", "-c", "import jsonschema"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if dependency.returncode:
            raise RuntimeError("The sync interpreter needs jsonschema; install maintenance/requirements.txt")
    manifest_path = vault / "_INDEX/source-hashes.json"
    manifest = strict_json_loads(manifest_path.read_text(encoding="utf-8-sig"))
    head = git(project, "rev-parse", "HEAD").decode().strip()
    rows = manifest["files"] + manifest["algorithm_references"] + [
        row for row in manifest.get("supporting_files", [])
        if row["path"].startswith("06_SOURCE/Code/")
    ]
    captured: dict[str, bytes] = {}
    changed: list[str] = []
    missing_in_commit: list[str] = []
    dirty_worktree_paths: list[str] = []
    for row in rows:
        relative = row.get("mirror", row.get("source", row.get("path")))
        if not relative.startswith("06_SOURCE/Code/"):
            raise RuntimeError(f"Unexpected source path in manifest: {relative}")
        repository_path = relative.removeprefix("06_SOURCE/Code/")
        if (not repository_path or "\\" in repository_path or ":" in repository_path
                or any(part in {"", ".", ".."} for part in repository_path.split("/"))):
            raise RuntimeError(f"Unsafe source path in manifest: {relative}")
        if git(project, "status", "--porcelain", "--untracked-files=all", "--", repository_path).strip():
            dirty_worktree_paths.append(relative)
            continue
        try:
            git(project, "show", f"HEAD:{repository_path}")
        except RuntimeError:
            missing_in_commit.append(relative)
            continue
        content = (project / repository_path).read_bytes()
        if relative.endswith(".py"):
            ast.parse(content.decode("utf-8-sig"), filename=repository_path)
        captured[relative] = content
        if digest(content) != row["sha256"]:
            changed.append(relative)
    registry_path = vault / "06_SOURCE/References/registry.json"
    registry = strict_json_loads(registry_path.read_text(encoding="utf-8-sig")) if registry_path.is_file() else None
    changed_references: dict[str, bytes] = {}
    dirty_reference_paths: list[str] = []
    missing_reference_commits: list[str] = []
    if registry is not None:
        for row in registry["references"]:
            relative = row["repository_relative_path"]
            if (not relative.startswith("engine/algorithms/") or "\\" in relative or ":" in relative
                    or any(part in {"", ".", ".."} for part in relative.split("/"))):
                raise RuntimeError(f"Unsafe reference path in registry: {relative}")
            if git(project, "status", "--porcelain", "--untracked-files=all", "--", relative).strip():
                dirty_reference_paths.append(relative)
                continue
            try:
                git(project, "show", f"HEAD:{relative}")
            except RuntimeError:
                missing_reference_commits.append(relative)
                continue
            content = (project / relative).read_bytes()
            if digest(content) != row["sha256"]:
                changed_references[relative] = content
    status = {
        "source_commit": head,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "changed_source_paths": changed,
        "changed_reference_paths": sorted(changed_references),
        "missing_in_commit": missing_in_commit,
        "dirty_worktree_paths": dirty_worktree_paths,
        "dirty_reference_paths": dirty_reference_paths,
        "missing_reference_commits": missing_reference_commits,
        "review_state": "needs_review" if (changed or changed_references or missing_in_commit
                                         or dirty_worktree_paths or dirty_reference_paths
                                         or missing_reference_commits) else "unchanged",
        "scope": "manifest-listed clean tracked source; exact working-tree bytes; no generated trading output",
    }
    if check:
        print(json.dumps(status, ensure_ascii=False))
        return status
    backups: dict[Path, bytes | None] = {}

    def remember(path: Path) -> None:
        if path not in backups:
            backups[path] = path.read_bytes() if path.is_file() else None

    def rollback() -> None:
        for path, original in reversed(list(backups.items())):
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)

    try:
        if changed_references and registry is not None:
            registry["source_commit"] = head
            for row in registry["references"]:
                content = changed_references.get(row["repository_relative_path"])
                if content is not None:
                    row["sha256"] = digest(content)
                    row["bytes"] = len(content)
                    row.update(reference_metadata(content))
                    row["name"] = Path(row["repository_relative_path"]).name
                    row["reconstruction_status"] = "needs_review"
            remember(registry_path)
            registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            registry_row = next((row for row in manifest.get("supporting_files", [])
                                 if row["path"] == "06_SOURCE/References/registry.json"), None)
            if registry_row is None:
                raise RuntimeError("Reference registry is not pinned in the source manifest")
            registry_bytes = registry_path.read_bytes()
            registry_row["sha256"] = digest(registry_bytes)
            registry_row["bytes"] = len(registry_bytes)
            remember(manifest_path)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if changed:
            for row in rows:
                relative = row.get("mirror", row.get("source", row.get("path")))
                if relative not in changed:
                    continue
                target = (vault / relative).resolve()
                if not target.is_relative_to((vault / "06_SOURCE/Code").resolve()):
                    raise RuntimeError("Source target escaped Vault")
                remember(target)
                target.write_bytes(captured[relative])
                row["sha256"] = digest(captured[relative])
                row["bytes"] = len(captured[relative])
                row["line_count"] = len(captured[relative].decode("utf-8-sig").splitlines())
                if row in manifest["algorithm_references"]:
                    row.update(reference_metadata(captured[relative]))
            manifest["source_commit"] = head
            manifest["created_utc"] = status["captured_utc"]
            remember(manifest_path)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for path in (vault / "06_SOURCE").rglob("*.md"):
                if "Code" in path.parts or path.stat().st_size == 0:
                    continue
                fields, body = frontmatter(path)
                dirty = False
                source_path = fields.get("source_path")
                if source_path in changed and "sha256" in fields:
                    fields["sha256"] = digest(captured[source_path])
                    dirty = True
                hashes = fields.get("external_source_hashes")
                if isinstance(hashes, dict):
                    for relative in set(hashes) & set(changed):
                        hashes[relative] = digest(captured[relative])
                        dirty = True
                if dirty:
                    remember(path)
                    write_note(path, fields, body)
        previous_path = vault / "_INDEX/sync-status.json"
        if previous_path.is_file() and not changed:
            previous = strict_json_loads(previous_path.read_text(encoding="utf-8-sig"))
            if previous.get("review_state") == "needs_review":
                status["review_state"] = "needs_review"
                status["changed_source_paths"] = previous.get("changed_source_paths", [])
        remember(previous_path)
        previous_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name in ("entities.json", "relations.json", "files.json", "source-map.json", "knowledge-graph.json"):
            remember(vault / "_INDEX" / name)
        for name in ("source-structure.json", "knowledge-model.json"):
            remember(vault / "_GENERATED" / name)
        result = subprocess.run([sys.executable, "-B", str(builder)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        status["index_check"] = "passed" if result.returncode == 0 else "failed"
        if result.returncode:
            rollback()
            status["review_state"] = "needs_review"
            status["index_error"] = (result.stderr or result.stdout)[-4000:] or f"Index builder exited {result.returncode} without output"
            status["rolled_back_source_paths"] = changed
        previous_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        rollback()
        raise
    print(json.dumps(status, ensure_ascii=False))
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = sync(args.project, args.vault, args.check)
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"Source sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(1 if result.get("index_check") == "failed" else 0)
