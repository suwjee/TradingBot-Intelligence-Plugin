"""Read-only byte identities for protected files."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True)
class FileIdentity:
    relative_path: str
    byte_count: int
    sha256: str


def snapshot_files(paths: Iterable[Path]) -> dict[str, FileIdentity]:
    """Snapshot explicit files and all files beneath explicit directories."""
    roots = [Path(path).resolve() for path in paths]
    result: dict[str, FileIdentity] = {}
    for root in roots:
        files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else [root]
        for path in files:
            if not path.is_file():
                raise FileNotFoundError(path)
            relative = path.relative_to(root).as_posix() if root.is_dir() else path.name
            key = f"{root.as_posix()}/{relative}" if root.is_dir() else root.as_posix()
            content = path.read_bytes()
            result[key] = FileIdentity(relative, len(content), hashlib.sha256(content).hexdigest())
    return result


def assert_unchanged(before: Mapping[str, FileIdentity], after: Mapping[str, FileIdentity]) -> None:
    """Raise with the exact paths whose presence or identity changed."""
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    if changed:
        raise AssertionError(f"Changed files: {', '.join(changed)}")
