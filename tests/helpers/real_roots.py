"""Explicit, read-only roots for real integration tests."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import unittest


@dataclass(frozen=True)
class RealRoots:
    vault: Path
    engine: Path | None


def require_real_roots(testcase: unittest.TestCase, *, engine_required: bool = False) -> RealRoots:
    """Require the real Vault, and require the Engine only for dependent tests."""
    requirements = (
        ("TRADINGBOT_KNOWLEDGE_VAULT", ("_INDEX/entities.json", "_INDEX/relations.json",
                                           "_INDEX/source-hashes.json", "06_SOURCE/References/registry.json")),
    )
    resolved = []
    for name, required in requirements:
        configured = os.environ.get(name)
        if not configured:
            raise unittest.SkipTest(f"Set {name} to the real checkout root")
        root = Path(configured).expanduser().resolve()
        if not root.is_dir():
            raise unittest.SkipTest(f"{name} is not an existing directory: {root}")
        for relative in required:
            if not (root / relative).exists():
                raise unittest.SkipTest(f"{name} is missing required resource: {relative}")
        resolved.append(root)
    configured_engine = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    if not engine_required:
        return RealRoots(resolved[0], None)
    if not configured_engine:
        raise unittest.SkipTest("Set TRADINGBOT_ENGINE_ROOT to the Engine checkout root")
    engine = Path(configured_engine).expanduser().resolve()
    if not engine.is_dir():
        raise unittest.SkipTest(f"TRADINGBOT_ENGINE_ROOT is not an existing directory: {engine}")
    if not (engine / "engine").is_dir():
        raise unittest.SkipTest("TRADINGBOT_ENGINE_ROOT is missing required resource: engine")
    return RealRoots(resolved[0], engine)
