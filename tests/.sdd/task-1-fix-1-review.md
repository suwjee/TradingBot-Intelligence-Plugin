# Task 1 fix round 1 scoped review package

## Findings under verification

1. Important: `build_fake_vault(..., relations=[...])` must write matching note-frontmatter relation fields and then pass `verify_package("knowledge")` for a two-entity, one-relation Vault.
2. Minor: an exception inside `plugin_reader()` must restore the process environment and cached Plugin-module state.

## Review basis

No commit is authorized. The files below are the current scope of the fix. The prior full Task 1 package is `tests/.sdd/task-1-review.md`.

## Implementer report including fix evidence

# Task 1 report: test foundation and synthetic Vault builder

Status: PASS for Task 1 foundation. No commits, staging, branches, worktrees,
dependency changes, Plugin runtime changes, Vault reads, or Production reads.

## Scope and files created

- `tests/__init__.py` and `tests/helpers/__init__.py`: importable test packages.
- `tests/helpers/fake_vault.py`: `EntitySpec`, `FakeVault`, `build_fake_vault`,
  `write_entity_note`, and `write_raw`. The builder writes a synthetic indexed
  authority note, user-supplied notes, deterministic entity and relation
  indexes, the schema marker, a reference registry, and SHA-256 manifest pins.
- `tests/helpers/plugin_runtime.py`: `plugin_reader` isolates import-time reader
  discovery with process-local environment and cached-module restoration.
- `tests/helpers/snapshots.py`: `FileIdentity`, `snapshot_files`, and
  `assert_unchanged` compare explicit file or directory byte identities.
- `tests/helpers/mcp_client.py`: `MCPTranscript` and a lazy-imported real stdio
  `run_mcp_session` client for later transport tests.
- `tests/unit/test_helpers.py`: five synthetic foundation tests.
- `tests/README.md`: suite architecture, prerequisites, environment, category
  and full-discovery commands, optional skip policy, and verification modes.

## Required RED evidence

Command, from `D:\My-Projects\TradingBot-Intelligence-Plugin`:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `1`. This was run after creating the first test and before creating
any helper implementation. Its failure was the expected missing module:

```text
test_helpers (unittest.loader._FailedTest.test_helpers) ... ERROR
ImportError: Failed to import test module: test_helpers
ModuleNotFoundError: No module named 'tests.helpers.fake_vault'
Ran 1 test in 0.000s
FAILED (errors=1)
```

## GREEN evidence

Command, from the same directory after helper and README implementation:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `0`. Exact final output:

```text
test_entity_index_is_deterministic_across_input_order (tests.unit.test_helpers.FoundationTests.test_entity_index_is_deterministic_across_input_order) ... ok
test_one_entity_vault_is_read_by_fresh_plugin_reader (tests.unit.test_helpers.FoundationTests.test_one_entity_vault_is_read_by_fresh_plugin_reader) ... ok
test_plugin_reader_restores_environment_and_module_cache (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_environment_and_module_cache) ... ok
test_reference_registry_and_source_pins_match_bytes (tests.unit.test_helpers.FoundationTests.test_reference_registry_and_source_pins_match_bytes) ... ok
test_snapshot_detects_changed_file (tests.unit.test_helpers.FoundationTests.test_snapshot_detects_changed_file) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.104s

OK
```

The pin test also calls the unmodified Plugin reader's
`verify_package("knowledge")` against temporary synthetic content and observes
`ok=True`.

## Self-review and limits

- All writes are test source under `tests/` or temporary synthetic Vault files
  created by test execution. No real Vault or Engine material is imported or
  copied by the helpers.
- Entity index serialization is sorted by stable ID; source and RAW pin order
  is sorted by path. Synthetic path writes reject traversal and drive syntax.
- `plugin_reader` restores the three environment variables and four relevant
  Plugin module cache entries even when a call raises. Because it temporarily
  changes process globals, callers should not overlap its contexts in threads.
- `run_mcp_session` was implemented from the Plugin's stdio client contract but
  not exercised by Task 1. The actual MCP transport remains for Task 5.
- Other planned category modules do not exist yet. A full-suite success claim
  would be premature; this result covers only the Task 1 foundation tests.

## Fix round 1: relation index and exception cleanup

The review found that supplied relations were written only to
`_INDEX/relations.json`. The reader reconstructs expected relations from note
frontmatter, so that fixture failed knowledge verification. The builder now
adds supplied edges to the corresponding note relation fields and derives the
index from the final note fields. It validates indexed endpoints and supported
relation types. Existing list values are copied before appending, so caller
frontmatter is not mutated.

Two tests were added: a two-entity `depends_on` fixture that requires
`verify_package("knowledge")` to succeed and a body exception inside
`plugin_reader()` that requires environment and module-cache restoration.

RED command, from the Plugin repository root:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `1`. The new exception test passed; the relation test exposed the
reported failure:

```text
test_plugin_reader_restores_state_after_body_exception ... ok
test_relation_argument_produces_verifiable_note_and_index ... FAIL
AssertionError: False is not true : ['_INDEX/relations.json']
Ran 7 tests in 0.262s
FAILED (failures=1)
```

GREEN command: the same focused command after the builder change. Exit code:
`0`. Exact final output:

```text
test_entity_index_is_deterministic_across_input_order (tests.unit.test_helpers.FoundationTests.test_entity_index_is_deterministic_across_input_order) ... ok
test_one_entity_vault_is_read_by_fresh_plugin_reader (tests.unit.test_helpers.FoundationTests.test_one_entity_vault_is_read_by_fresh_plugin_reader) ... ok
test_plugin_reader_restores_environment_and_module_cache (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_environment_and_module_cache) ... ok
test_plugin_reader_restores_state_after_body_exception (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_state_after_body_exception) ... ok
test_reference_registry_and_source_pins_match_bytes (tests.unit.test_helpers.FoundationTests.test_reference_registry_and_source_pins_match_bytes) ... ok
test_relation_argument_produces_verifiable_note_and_index (tests.unit.test_helpers.FoundationTests.test_relation_argument_produces_verifiable_note_and_index) ... ok
test_snapshot_detects_changed_file (tests.unit.test_helpers.FoundationTests.test_snapshot_detects_changed_file) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.175s

OK
```

Files changed in this round: `tests/helpers/fake_vault.py`,
`tests/unit/test_helpers.py`, and this report. No production source was changed.


## Current amended files

## tests/helpers/fake_vault.py (current after fix round 1)

```
"""Build small synthetic Vaults without consulting real knowledge or data."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


_RELATION_FIELDS = ("calculated_by", "implemented_by", "depends_on", "produces",
                    "implements", "affects", "parent_of", "child_of", "relates_to",
                    "supports", "orchestrates", "related_entities")


@dataclass(frozen=True)
class EntitySpec:
    id: str
    file: str
    type: str
    status: str
    authority: str
    title: str
    body: str
    frontmatter: Mapping[str, object] = field(default_factory=dict)

    @property
    def relative_note_path(self) -> str:
        return self.file


@dataclass(frozen=True)
class FakeVault:
    root: Path
    entities: Mapping[str, dict]
    relations: Sequence[dict[str, str]]
    manifest: Mapping[str, object]


def _relative_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Synthetic path must be Vault-relative POSIX text")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Synthetic path must be normalized")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Synthetic path escapes temporary Vault")
    return path


def _write(root: Path, relative: str, content: bytes) -> Path:
    path = _relative_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _json_bytes(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def write_entity_note(root: Path, entity: EntitySpec) -> Path:
    """Write JSON-valued frontmatter accepted by the Plugin reader."""
    fields = {"id": entity.id, "type": entity.type, "status": entity.status,
              "authority": entity.authority, "title": entity.title, **entity.frontmatter}
    header = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in fields.items())
    return _write(root, entity.file, f"---\n{header}\n---\n{entity.body}\n".encode("utf-8"))


def write_raw(root: Path, relative: str, content: bytes) -> Path:
    """Write synthetic RAW bytes under the reader's allowed RAW directory."""
    if not relative.startswith("08_DATA/Raw/"):
        raise ValueError("RAW path must be within 08_DATA/Raw/")
    return _write(root, relative, content)


def _pin(root: Path, relative: str, key: str = "path") -> dict[str, object]:
    content = _relative_path(root, relative).read_bytes()
    return {key: relative, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def build_fake_vault(
    root: Path,
    entities: Sequence[EntitySpec],
    *,
    relations: Sequence[dict[str, str]] = (),
    source_files: Mapping[str, bytes] = {},
    references: Sequence[dict] = (),
    raw_files: Mapping[str, bytes] = {},
) -> FakeVault:
    """Create the minimal Plugin-compatible, pinned synthetic Vault layout."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    authority = EntitySpec("system.authority-model", "00_SYSTEM/AUTHORITY_MODEL.md",
                           "system", "active", "canonical", "Synthetic authority model",
                           "Synthetic authority metadata only.")
    all_entities = [authority, *entities]
    ids = [item.id for item in all_entities]
    files = [item.file for item in all_entities]
    if len(ids) != len(set(ids)) or len(files) != len(set(files)):
        raise ValueError("Synthetic entities need unique IDs and note paths")
    by_id = {item.id: item for item in all_entities}
    note_fields = {item.id: dict(item.frontmatter) for item in all_entities}
    for edge in relations:
        source, target, relation_type = edge["from"], edge["to"], edge["type"]
        if source not in by_id or target not in by_id:
            raise ValueError("Synthetic relation endpoint is not indexed")
        if relation_type not in _RELATION_FIELDS:
            raise ValueError("Synthetic relation type is not supported")
        field_name = "related_entities" if relation_type == "relates_to" else relation_type
        existing = note_fields[source].get(field_name, [])
        if not isinstance(existing, list):
            raise ValueError("Synthetic relation frontmatter must contain a list")
        targets = list(existing)
        targets.append(target)
        note_fields[source][field_name] = targets
    all_entities = [replace(item, frontmatter=note_fields[item.id]) for item in all_entities]
    rows: dict[str, dict] = {}
    for item in sorted(all_entities, key=lambda value: value.id):
        write_entity_note(root, item)
        row = {"file": item.file, "type": item.type, "status": item.status,
               "authority": item.authority, "title": item.title}
        for key in ("valid_for_reasoning", "implementation_validity",
                    "affected_by_known_invalid_order_route"):
            if key in item.frontmatter:
                row[key] = item.frontmatter[key]
        rows[item.id] = row
    _write(root, "_INDEX/entities.json", _json_bytes({"entities": rows}))
    edges = []
    for item in all_entities:
        for field_name in _RELATION_FIELDS:
            for target in item.frontmatter.get(field_name, []):
                edges.append({"from": item.id,
                              "type": "relates_to" if field_name == "related_entities" else field_name,
                              "to": target})
    edges.sort(key=lambda edge: (edge["from"], edge["type"], edge["to"]))
    _write(root, "_INDEX/relations.json", _json_bytes({"relations": edges}))
    _write(root, "_SCHEMA/note.schema.json", _json_bytes(
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}))
    _write(root, "06_SOURCE/References/registry.json", _json_bytes(
        {"schema_version": 1, "references": list(references)}))
    source_pins = []
    for relative, content in sorted(source_files.items()):
        if not relative.startswith("06_SOURCE/Code/"):
            raise ValueError("Source path must be within 06_SOURCE/Code/")
        _write(root, relative, content)
        source_pins.append(_pin(root, relative, "mirror"))
    raw_pins = []
    for relative, content in sorted(raw_files.items()):
        write_raw(root, relative, content)
        raw_pins.append(_pin(root, relative))
    manifest = {"files": source_pins, "algorithm_references": [],
                "supporting_files": [_pin(root, "06_SOURCE/References/registry.json"), *raw_pins]}
    _write(root, "_INDEX/source-hashes.json", _json_bytes(manifest))
    return FakeVault(root, rows, edges, manifest)

```

## tests/helpers/plugin_runtime.py (current after fix round 1)

```
"""Load the Plugin reader against a process-local temporary Vault."""

from __future__ import annotations

from contextlib import contextmanager
import importlib
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterator


_ENV_KEYS = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
             "TRADINGBOT_PLUGIN_CONFIG")
_MODULES = ("vault_reader", "vault_cli", "mcp_server", "runtime_doctor")


@contextmanager
def plugin_reader(vault_root: Path, *, engine_root: Path | None = None) -> Iterator[ModuleType]:
    """Fresh import with restored environment and Plugin module cache on exit."""
    previous_env = {key: os.environ.get(key) for key in _ENV_KEYS}
    previous_modules = {key: sys.modules.get(key) for key in _MODULES}
    plugin_root = str(Path(__file__).resolve().parents[2])
    inserted = plugin_root not in sys.path
    if inserted:
        sys.path.insert(0, plugin_root)
    try:
        os.environ["TRADINGBOT_KNOWLEDGE_VAULT"] = str(Path(vault_root).resolve())
        os.environ["TRADINGBOT_PLUGIN_CONFIG"] = str(Path(vault_root) / "no-user-config.json")
        if engine_root is None:
            os.environ.pop("TRADINGBOT_ENGINE_ROOT", None)
        else:
            os.environ["TRADINGBOT_ENGINE_ROOT"] = str(Path(engine_root).resolve())
        for name in _MODULES:
            sys.modules.pop(name, None)
        yield importlib.import_module("vault_reader")
    finally:
        for name in _MODULES:
            sys.modules.pop(name, None)
            if previous_modules[name] is not None:
                sys.modules[name] = previous_modules[name]
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if inserted:
            sys.path.remove(plugin_root)

```

## tests/unit/test_helpers.py (current after fix round 1)

```
"""Contracts for the test-only foundation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import os
import sys
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class FoundationTests(unittest.TestCase):
    def sample(self):
        return EntitySpec(id="system.sample", file="00_SYSTEM/Sample.md", type="system",
                          status="active", authority="canonical", title="Sample",
                          body="Synthetic sample.")

    def test_one_entity_vault_is_read_by_fresh_plugin_reader(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("system.sample")["id"], "system.sample")

    def test_entity_index_is_deterministic_across_input_order(self):
        other = EntitySpec(id="system.alpha", file="00_SYSTEM/Alpha.md", type="system",
                           status="active", authority="canonical", title="Alpha", body="Synthetic alpha.")
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            build_fake_vault(Path(first), [self.sample(), other])
            build_fake_vault(Path(second), [other, self.sample()])
            left = (Path(first) / "_INDEX/entities.json").read_bytes()
            right = (Path(second) / "_INDEX/entities.json").read_bytes()
            self.assertEqual(left, right)
            self.assertEqual(list(json.loads(left)["entities"]),
                             ["system.alpha", "system.authority-model", "system.sample"])

    def test_reference_registry_and_source_pins_match_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            built = build_fake_vault(root, [self.sample()],
                                     source_files={"06_SOURCE/Code/sample.py": b"x = 1\n"})
            pins = built.manifest["files"] + built.manifest["supporting_files"]
            for pin in pins:
                relative = pin.get("mirror", pin.get("path"))
                data = (root / relative).read_bytes()
                self.assertEqual(pin["bytes"], len(data))
                self.assertEqual(pin["sha256"], hashlib.sha256(data).hexdigest())
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])

    def test_relation_argument_produces_verifiable_note_and_index(self):
        other = EntitySpec(id="system.other", file="00_SYSTEM/Other.md", type="system",
                           status="active", authority="canonical", title="Other", body="Synthetic other.")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample(), other], relations=[
                {"from": "system.sample", "type": "depends_on", "to": "system.other"}])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
                self.assertTrue(result["ok"], result["errors"])
                fields, _ = reader._frontmatter(reader.get_entity("system.sample")["content"])
                self.assertEqual(fields["depends_on"], ["system.other"])

    def test_plugin_reader_restores_environment_and_module_cache(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            keys = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
                    "TRADINGBOT_PLUGIN_CONFIG")
            before = {key: os.environ.get(key) for key in keys}
            prior_reader = sys.modules.get("vault_reader")
            with plugin_reader(root) as reader:
                self.assertEqual(reader.ROOT, root.resolve())
                self.assertEqual(os.environ["TRADINGBOT_KNOWLEDGE_VAULT"], str(root.resolve()))
                self.assertNotIn("TRADINGBOT_ENGINE_ROOT", os.environ)
            self.assertEqual({key: os.environ.get(key) for key in keys}, before)
            self.assertIs(sys.modules.get("vault_reader"), prior_reader)

    def test_plugin_reader_restores_state_after_body_exception(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            keys = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
                    "TRADINGBOT_PLUGIN_CONFIG")
            before = {key: os.environ.get(key) for key in keys}
            prior_reader = sys.modules.get("vault_reader")
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with plugin_reader(root) as reader:
                    self.assertEqual(reader.ROOT, root.resolve())
                    raise RuntimeError("synthetic failure")
            self.assertEqual({key: os.environ.get(key) for key in keys}, before)
            self.assertIs(sys.modules.get("vault_reader"), prior_reader)

    def test_snapshot_detects_changed_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"one")
            before = snapshot_files([path])
            path.write_bytes(b"two")
            after = snapshot_files([path])
            with self.assertRaisesRegex(AssertionError, "sample.txt"):
                assert_unchanged(before, after)

```

