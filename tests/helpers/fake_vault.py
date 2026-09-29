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
              "authority": entity.authority, "title": entity.title,
              "related_entities": [], "source_reference": [], **entity.frontmatter}
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
    reference_files: Mapping[str, bytes] = {},
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
        note = write_entity_note(root, item)
        row = {"file": item.file, "id": item.id, "type": item.type,
               "status": item.status, "authority": item.authority, "title": item.title,
               "related_entities": [], "source_reference": [], **item.frontmatter}
        data = note.read_bytes()
        row["content_sha256"] = hashlib.sha256(data).hexdigest()
        row["content_bytes"] = len(data)
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
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
         "required": ["id", "type", "status", "authority", "title", "related_entities", "source_reference"],
         "properties": {"id": {"type": "string"}, "type": {"type": "string"},
                        "status": {"type": "string"}, "authority": {"type": "string"},
                        "title": {"type": "string"}, "related_entities": {"type": "array"},
                        "source_reference": {"type": "array"},
                        "valid_for_reasoning": {"type": "boolean"}}}))
    _write(root, "06_SOURCE/References/registry.json", _json_bytes(
        {"schema_version": 1, "references": list(references)}))
    source_pins = []
    for relative, content in sorted(source_files.items()):
        if not relative.startswith("06_SOURCE/Code/"):
            raise ValueError("Source path must be within 06_SOURCE/Code/")
        _write(root, relative, content)
        source_pins.append(_pin(root, relative, "mirror"))
    reference_pins = []
    for relative, content in sorted(reference_files.items()):
        if not relative.startswith("06_SOURCE/Code/engine/algorithms/"):
            raise ValueError("Reference path must be within captured Engine algorithms")
        _write(root, relative, content)
        reference_pins.append(_pin(root, relative, "source"))
    raw_pins = []
    for relative, content in sorted(raw_files.items()):
        write_raw(root, relative, content)
        raw_pins.append(_pin(root, relative))
    manifest = {"files": source_pins, "algorithm_references": reference_pins,
                "supporting_files": [_pin(root, "06_SOURCE/References/registry.json"), *raw_pins]}
    _write(root, "_INDEX/source-hashes.json", _json_bytes(manifest))
    return FakeVault(root, rows, edges, manifest)
