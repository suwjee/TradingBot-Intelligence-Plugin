"""Read-only, Vault-root-relative access to the captured knowledge package."""
from __future__ import annotations

from pathlib import Path
import bisect
from functools import lru_cache
import hashlib
import json
import os
import re
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from integrity import metadata_json, strict_json_decoder, strict_json_loads


class VaultError(RuntimeError):
    """An expected configuration or integrity failure with a stable code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def error_payload(exc: Exception) -> dict:
    """Translate expected reader failures to a stable machine-readable shape."""
    if isinstance(exc, VaultError):
        code = exc.code
    elif isinstance(exc, KeyError):
        code = "INVALID_VAULT"
    elif isinstance(exc, OSError):
        code = "DEPENDENCY_UNAVAILABLE"
    elif isinstance(exc, ValueError):
        message = str(exc)
        if message.startswith("Unknown entity:"):
            code = "ENTITY_NOT_FOUND"
        elif "reference" in message.lower() and "identity" in message.lower():
            code = "REFERENCE_HASH_MISMATCH"
        elif "Evidence hash" in message:
            code = "SOURCE_HASH_MISMATCH"
        elif "Stale" in message:
            code = "INDEX_STALE"
        elif any(term in message for term in ("Path escapes", "Path must be", "Unsafe reference")):
            code = "PATH_OUTSIDE_ALLOWED_ROOT"
        elif "time range" in message.lower():
            code = "INVALID_TIME_RANGE"
        elif "exceeds response byte limit" in message:
            code = "RESPONSE_TOO_LARGE"
        elif "reference" in message.lower() and "unavailable" in message.lower():
            code = "REFERENCE_NOT_FOUND"
        else:
            code = "INVALID_REQUEST"
    else:
        code = "INTERNAL_ERROR"
    message = str(exc) if code not in {"INTERNAL_ERROR", "DEPENDENCY_UNAVAILABLE"} else (
        "Required resource unavailable" if code == "DEPENDENCY_UNAVAILABLE" else "Internal reader error")
    return {"ok": False, "error": {"code": code, "message": message}}


def vault_config_path() -> Path:
    configured = os.environ.get("TRADINGBOT_PLUGIN_CONFIG")
    return (Path(configured).expanduser() if configured else
            Path.home() / ".config" / "tradingbot-intelligence" / "vault.json")


def locate_vault() -> Path:
    configured = os.environ.get("TRADINGBOT_KNOWLEDGE_VAULT")
    candidates = [Path(configured)] if configured else []
    if not configured:
        config_path = vault_config_path()
        if config_path.is_file():
            try:
                config = strict_json_loads(config_path.read_text(encoding="utf-8-sig"))
                candidates.append(Path(config["vault_root"]))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise VaultError("INVALID_CONFIG", "Vault configuration is unreadable") from exc
        candidates.append(Path(__file__).resolve().parent.parent / "TradingBot-Knowledge")
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        if not root.is_dir():
            if configured:
                raise VaultError("VAULT_NOT_FOUND", f"Configured Vault root does not exist: {root}")
            continue
        required = ("_INDEX/entities.json", "_INDEX/relations.json",
                    "_INDEX/source-hashes.json", "_SCHEMA/note.schema.json",
                    "00_SYSTEM/AUTHORITY_MODEL.md", "06_SOURCE/References/registry.json")
        resources = {relative: (root / relative).resolve() for relative in required}
        if any(not path.is_relative_to(root) for path in resources.values()):
            raise VaultError("PATH_OUTSIDE_ALLOWED_ROOT", "Bootstrap resource escapes the Vault root")
        missing = [relative for relative, path in resources.items() if not path.is_file()]
        if missing:
            if configured:
                raise VaultError("INVALID_VAULT", f"Missing required files: {', '.join(missing)}")
            continue
        try:
            entities = strict_json_loads(resources[required[0]].read_text(encoding="utf-8-sig"))
            relations = strict_json_loads(resources[required[1]].read_text(encoding="utf-8-sig"))
            schema = strict_json_loads(resources[required[3]].read_text(encoding="utf-8-sig"))
            registry = strict_json_loads(resources[required[5]].read_text(encoding="utf-8-sig"))
            manifest = strict_json_loads(resources[required[2]].read_text(encoding="utf-8-sig"))
            if (not all(isinstance(item, dict) for item in (entities, relations, schema, registry, manifest))
                    or not isinstance(entities.get("entities"), dict)
                    or not isinstance(relations.get("relations"), list)
                    or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
                    or registry.get("schema_version") != 1):
                raise ValueError("Unsupported schema or index structure")
        except (OSError, ValueError, TypeError) as exc:
            raise VaultError("INVALID_VAULT", "Vault schema or index is invalid or incompatible") from exc
        return root
    raise VaultError("VAULT_NOT_FOUND", "Configure a cloned Vault with scripts/configure_vault.py or TRADINGBOT_KNOWLEDGE_VAULT")


ROOT = locate_vault()
INDEX = ROOT / "_INDEX"

RELATION_FIELDS = ("calculated_by", "implemented_by", "depends_on", "produces",
                   "implements", "affects", "parent_of", "child_of", "relates_to",
                   "supports", "orchestrates", "related_entities")

@lru_cache(maxsize=512)
def _cached_text(path: str, mtime_ns: int, ctime_ns: int, size: int) -> str:
    """Cache file text by observed identity; no query or authority state is cached."""
    return Path(path).read_text(encoding="utf-8-sig")


def _read_text(path: Path) -> str:
    stamp = path.stat()
    return _cached_text(str(path), stamp.st_mtime_ns, stamp.st_ctime_ns, stamp.st_size)


def _json(relative: str) -> dict:
    try:
        value = strict_json_loads(_inside(relative, "").read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value
    except (ValueError, TypeError) as exc:
        raise VaultError("INVALID_VAULT", f"Invalid trusted JSON: {relative}: {exc}") from exc


def _inside(relative: str, prefix: str) -> Path:
    if (not isinstance(relative, str) or not relative.startswith(prefix)
            or "\\" in relative or ":" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("Path must be a normalized path inside the Vault")
    path = (ROOT / relative).resolve()
    if (not path.is_relative_to(ROOT.resolve())
            or not path.is_relative_to((ROOT / prefix).resolve())):
        raise ValueError("Path escapes the Vault")
    return path


def _entities() -> dict:
    entities = _json("_INDEX/entities.json")["entities"]
    contract = _json("_INDEX/source-hashes.json").get("current_contract")
    if contract is not None:
        try:
            if not isinstance(contract, dict) or not isinstance(entities, dict):
                raise ValueError("Current contract and entity index must be objects")
            declared = contract.get("entities", {})
            if not isinstance(declared, dict):
                raise ValueError("Current entity contract must be an object")
            if contract.get("closed_entity_inventory") and set(declared) != set(entities):
                raise ValueError("Current entity inventory differs from its declared contract")
            for ident, constraints in declared.items():
                if ident not in entities or not isinstance(constraints, dict):
                    raise ValueError(f"Missing current contract entity: {ident}")
                for field, value in constraints.items():
                    if metadata_json(entities[ident].get(field)) != metadata_json(value):
                        raise ValueError(f"Current contract metadata mismatch: {ident}:{field}")
            for kind in contract.get("empty_entity_types", []):
                if any(row["type"] == kind for row in entities.values()):
                    raise ValueError(f"Current contract requires empty entity type: {kind}")
            for selector in contract.get("empty_entity_filters", []):
                if not isinstance(selector, dict) or not selector:
                    raise ValueError("Empty entity filter must be a nonempty metadata object")
                if any(all(metadata_json(row.get(key)) == metadata_json(value)
                           for key, value in selector.items()) for row in entities.values()):
                    raise ValueError(f"Current contract requires empty entity filter: {selector}")
        except (ValueError, TypeError, KeyError) as exc:
            raise VaultError("INVALID_VAULT", f"Current contract validation: {exc}") from exc
    return entities


def _reference_registry() -> dict:
    relative = "06_SOURCE/References/registry.json"
    path = _inside(relative, "06_SOURCE/References/")
    manifest = _json("_INDEX/source-hashes.json")
    row = next((item for item in manifest.get("supporting_files", []) if item["path"] == relative), None)
    if row is None or not path.is_file():
        raise ValueError("Reference registry is not pinned in the Vault manifest")
    data = path.read_bytes()
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("Reference registry differs from its pinned manifest identity")
    registry = strict_json_loads(data)
    references = registry.get("references") if isinstance(registry, dict) else None
    required = {"id", "local_path", "repository_relative_path", "sha256", "bytes"}
    if (not isinstance(registry, dict) or registry.get("schema_version") != 1 or not isinstance(references, list)
            or any(not isinstance(item, dict) or not required <= item.keys()
                   or not all(isinstance(item[key], str) for key in required - {"bytes"})
                   or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                   or not isinstance(item["bytes"], int) or isinstance(item["bytes"], bool)
                   or item["bytes"] < 0 for item in references)
            or len({item["id"] for item in references}) != len(references)):
        raise VaultError("INVALID_VAULT", "Malformed reference registry")
    return registry


def _quarantined(entity_id: str, row: dict) -> bool:
    return (row.get("valid_for_reasoning") is False
            or row.get("implementation_validity") == "known-invalid"
            or row.get("authority") == "non-canonical"
            or row.get("status") in {"draft", "pending", "pending-fix", "proposed",
                                     "deprecated", "superseded", "archived", "historical"})


def _warning(entity_id: str, row: dict) -> str | None:
    if row.get("implementation_validity") == "known-invalid":
        return "Known-invalid or unresolved knowledge: diagnostic evidence only; do not use for trading reasoning or regression baselines."
    if row.get("affected_by_known_invalid_order_route"):
        return "Mixed source evidence: invalid dependent regions require route-specific review."
    if row.get("reference_agreement") in {"conflict", "ambiguous"}:
        return "Source-backed executable facts and documented Reference claims differ; inspect the recorded conflict before interpreting intended behavior."
    if _quarantined(entity_id, row):
        return "Non-canonical or unresolved knowledge: inspect status and evidence before use."
    return None


@lru_cache(maxsize=512)
def _parsed_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        raise ValueError("Knowledge note has no complete frontmatter")
    header, body = content[4:].split("\n---\n", 1)
    fields = {}
    for line in header.splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        if key in fields:
            raise ValueError(f"Duplicate frontmatter field: {key}")
        fields[key] = strict_json_loads(value.strip())
    return fields, body


def _frontmatter(content: str) -> tuple[dict, str]:
    fields, body = _parsed_frontmatter(content)
    return dict(fields), body


@lru_cache(maxsize=64)
def _schema_validator(content: str):
    try:
        schema = strict_json_loads(content)
        Draft202012Validator.check_schema(schema)
    except (ValueError, SchemaError) as exc:
        raise VaultError("INVALID_VAULT", "Invalid frontmatter schema") from exc
    return Draft202012Validator(schema)


def _read_indexed_note(entity_id: str, row: dict) -> str:
    data = _inside(row["file"], "").read_bytes()
    if (_json("_INDEX/source-hashes.json").get("current_contract", {}).get("require_note_identity")
            and not {"content_sha256", "content_bytes"} <= row.keys()):
        raise ValueError(f"Stale entity index: required note identity missing: {entity_id}")
    if ("content_sha256" in row or "content_bytes" in row) and (
            row.get("content_sha256") != hashlib.sha256(data).hexdigest()
            or type(row.get("content_bytes")) is not int or row["content_bytes"] != len(data)):
        raise ValueError(f"Stale entity index: note content changed: {entity_id}")
    content = data.decode("utf-8-sig")
    fields, _ = _frontmatter(content)
    derived = {"file", "content_sha256", "content_bytes"}
    expected = {"id": entity_id, **{key: value for key, value in row.items() if key not in derived}}
    if (expected.get("id") != entity_id
            or metadata_json(fields) != metadata_json(expected)):
        raise ValueError(f"Stale entity index: {entity_id}")
    for name in ("note", fields.get("type")):
        schema_path = _inside(f"_SCHEMA/{name}.schema.json", "_SCHEMA/")
        if schema_path.is_file():
            validator = _schema_validator(_read_text(schema_path))
            failures = sorted(validator.iter_errors(fields), key=lambda error: str(error.path))
            if failures:
                raise VaultError("INVALID_VAULT", f"Invalid frontmatter: {entity_id}: {failures[0].message}")
    return content


def _name_index(entities: dict) -> dict[str, str]:
    """Resolve only validated metadata; no name can shadow another physical ID."""
    names = {}
    for entity_id, row in sorted(entities.items()):
        _read_indexed_note(entity_id, row)
        aliases = row.get("aliases", [])
        if not isinstance(aliases, list):
            raise VaultError("INVALID_VAULT", f"Invalid aliases: {entity_id}")
        for label in [entity_id, row.get("name", row["title"]), *aliases]:
            if not isinstance(label, str) or not label.strip():
                raise VaultError("INVALID_VAULT", f"Invalid entity name: {entity_id}")
            key = label.strip().casefold()
            if key in names and names[key] != entity_id:
                raise VaultError("INVALID_VAULT", f"Ambiguous entity name: {label}")
            names[key] = entity_id
    return names


def _resolve_entity(query: str, entities: dict) -> str:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Supply an entity ID, canonical name or alias")
    entity_id = _name_index(entities).get(query.strip().casefold())
    if entity_id is None:
        raise ValueError(f"Unknown entity: {query}")
    return entity_id


def _assert_evidence_current(row: dict) -> None:
    """Check declared knowledge owners before returning their current semantics."""
    references = [*row.get("source_reference", []), *row.get("source_refs", [])]
    if row.get("source_path"):
        references.append(row["source_path"])
    algorithm_refs = row.get("algorithm_reference", [])
    if not references and not algorithm_refs:
        return
    manifest = _json("_INDEX/source-hashes.json")
    pins = manifest["files"] + manifest["algorithm_references"] + manifest.get("supporting_files", [])
    by_path = {item.get("mirror", item.get("source", item.get("path"))): item for item in pins}
    registry = _reference_registry() if algorithm_refs else {"references": []}
    by_id = {item["id"]: item for item in registry["references"]}
    references.extend(by_id[value]["local_path"] if value in by_id else value for value in algorithm_refs)
    for relative in sorted({value.partition("#")[0] for value in references}):
        path = _inside(relative, "06_SOURCE/Code/")
        pin = by_path.get(relative)
        if pin is None:
            raise VaultError("SOURCE_HASH_MISMATCH", f"Knowledge evidence is not pinned: {relative}")
        data = path.read_bytes()
        if len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise VaultError("SOURCE_HASH_MISMATCH", f"Knowledge evidence identity differs: {relative}")
        configured = os.environ.get("TRADINGBOT_ENGINE_ROOT")
        repository_relative = pin.get("repository_relative_path", relative.removeprefix("06_SOURCE/Code/"))
        if relative.startswith("06_SOURCE/Code/engine/"):
            canonical_relative = relative.removeprefix("06_SOURCE/Code/")
            if repository_relative != canonical_relative:
                raise ValueError("Unsafe reference or Source registry path: captured Engine mapping differs")
        if configured and repository_relative.startswith("engine/"):
            if ("\\" in repository_relative or ":" in repository_relative
                    or any(part in {"", ".", ".."} for part in repository_relative.split("/"))):
                raise ValueError("Unsafe reference or Source registry path")
            root = Path(configured).expanduser().resolve()
            external = (root / repository_relative).resolve()
            if not external.is_relative_to(root) or not external.is_relative_to((root / "engine").resolve()):
                raise ValueError("Path escapes the configured Engine")
            if (not external.is_file() or external.read_bytes() != data):
                raise VaultError("SOURCE_HASH_MISMATCH", f"External Engine evidence differs: {repository_relative}")
    for value in algorithm_refs:
        reference = by_id.get(value) or next((item for item in registry["references"]
                                            if item["local_path"] == value.partition("#")[0]), None)
        if reference is None:
            raise VaultError("INVALID_VAULT", "Algorithm Reference is not registered")
        _local_reference(reference)
        _external_reference(reference)


def _sync_review_state() -> str:
    path = ROOT / "_INDEX/sync-status.json"
    if not path.is_file():
        return "snapshot_without_commit_pin"
    return _json("_INDEX/sync-status.json").get("review_state", "unknown")


def _note(entity_id: str) -> tuple[dict, str]:
    row = _entities().get(entity_id)
    if row is None:
        raise ValueError(f"Unknown entity: {entity_id}")
    return row, _read_indexed_note(entity_id, row)


def _fixture_source_review_issues(entities: dict) -> tuple[list[str], list[str], list[str]]:
    """Return strict errors and explicitly declared pending fixture-source drift."""
    errors: list[str] = []
    warnings: list[str] = []
    known_pending: list[str] = []
    for entity_id, row in entities.items():
        if row.get("type") != "case":
            continue
        try:
            fields, _ = _frontmatter(_read_indexed_note(entity_id, row))
            fixture = _inside(fields["source_fixture"], "")
            if not fixture.is_file():
                errors.append(f"fixture_source_missing:{entity_id}")
                continue
            actual_sha256 = hashlib.sha256(fixture.read_bytes()).hexdigest()
            if actual_sha256 != fields["source_fixture_sha256"]:
                issue = f"fixture_source_sha_mismatch:{entity_id}"
                if fields.get("source_fixture_review") == "pending-manual-review":
                    known_pending.append(issue)
                    warnings.append(f"KNOWN_PENDING: {issue}")
                else:
                    errors.append(issue)
            fixture_lines = fixture.read_text(encoding="utf-8-sig").splitlines()
            fixture_line = fields["source_fixture_line"]
            if not isinstance(fixture_line, int) or fixture_line < 1 or fixture_line > len(fixture_lines):
                errors.append(f"fixture_source_line_out_of_range:{entity_id}")
                continue
            if fixture_lines[fixture_line - 1] != f"### {fields['title']}":
                errors.append(f"fixture_source_heading_mismatch:{entity_id}")
        except (OSError, ValueError, KeyError, TypeError, VaultError):
            errors.append(f"fixture_source_invalid:{entity_id}")
    return errors, warnings, known_pending


def _reference_identity(row: dict, data: bytes, label: str) -> None:
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError(f"{label} reference identity differs from the pinned registry")
    text = data.decode("utf-8-sig")
    version = re.search(r"\*\*Document Version:\*\* `([^`]+)`", text)
    if version and version[1] != row.get("version"):
        raise ValueError(f"{label} reference version differs from the pinned registry")
    direction = re.search(r"\*\*Target Direction:\*\* `([^`]+)`", text)
    if direction and direction[1].casefold() != str(row.get("direction", "")).casefold():
        raise ValueError(f"{label} reference direction differs from the pinned registry")


def _local_reference(row: dict) -> bytes:
    relative = row["local_path"]
    path = _inside(relative, "06_SOURCE/Code/engine/algorithms/")
    if not path.is_file():
        raise ValueError("Local reference file is unavailable")
    data = path.read_bytes()
    _reference_identity(row, data, "Local")
    pins = [item for item in _json("_INDEX/source-hashes.json")["algorithm_references"]
            if item.get("mirror", item.get("source")) == relative]
    if (len(pins) != 1 or pins[0]["sha256"] != row["sha256"]
            or pins[0]["bytes"] != row["bytes"]):
        raise ValueError("Local reference identity differs from the source manifest")
    for field in ("version", "direction"):
        if field in pins[0] and pins[0][field] != row.get(field):
            raise ValueError(f"Local reference {field} differs from the source manifest")
    return data


def _external_reference(row: dict) -> bytes | None:
    configured = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    if not configured:
        return None
    relative = row["repository_relative_path"]
    if (not relative.startswith("engine/algorithms/") or "\\" in relative or ":" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("Unsafe reference registry path")
    root = Path(configured).expanduser().resolve()
    path = (root / relative).resolve()
    if (not path.is_relative_to(root) or not path.is_relative_to((root / "engine/algorithms").resolve())
            or not path.is_file()):
        raise ValueError("Configured reference file is unavailable")
    data = path.read_bytes()
    _reference_identity(row, data, "External")
    return data


def _local_reference_availability(registry: dict, failures: list[str]) -> dict[str, str]:
    availability = {}
    for item in registry["references"]:
        try:
            _local_reference(item)
            availability[item["id"]] = "verified"
        except (OSError, ValueError, KeyError, TypeError):
            availability[item["id"]] = "unavailable_or_mismatched"
            failures.append(f"local_reference_identity:{item['id']}")
    return availability


def _external_reference_availability(registry: dict, failures: list[str]) -> dict[str, str]:
    """Verify configured external reference evidence when its root is available."""
    availability: dict[str, str] = {}
    configured_engine = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    for item in registry["references"]:
        if not configured_engine:
            availability[item["id"]] = "optional_not_configured"
            continue
        try:
            _external_reference(item)
            availability[item["id"]] = "verified"
        except (OSError, ValueError, KeyError):
            availability[item["id"]] = "unavailable"
            failures.append(f"reference_unavailable:{item['id']}")
    return availability


def search(query: str, limit: int = 8, include_quarantined: bool = False,
           *, entity_type: str | None = None, authority: str | None = None,
           status: str | None = None, include_noncanonical: bool = False,
           include_pending: bool = False, offset: int = 0) -> list[dict]:
    if not isinstance(query, str) or not re.search(r"\w", query):
        raise ValueError("Supply a search term")
    terms = [term.casefold() for term in re.findall(r"\w+", query) if len(term) > 1]
    entities = _entities()
    exact = _name_index(entities).get(query.strip().casefold())
    limit = max(1, min(int(limit), 25))
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("Search offset must be a nonnegative integer")
    hits = []
    for entity_id, row in entities.items():
        if entity_type is not None and row.get("type") != entity_type:
            continue
        if authority is not None and row.get("authority") != authority:
            continue
        if status is not None and row.get("status") != status:
            continue
        explicitly_included = include_quarantined or include_noncanonical or (
            include_pending and row.get("status") in {"pending", "pending-fix", "draft", "proposed"})
        if _quarantined(entity_id, row) and not explicitly_included:
            continue
        note = _read_indexed_note(entity_id, row)
        body = _frontmatter(note)[1]
        title = row["title"].casefold()
        lower = body.casefold()
        aliases = " ".join(row.get("aliases", [])).casefold()
        name = row.get("name", "").casefold()
        score = (100 if entity_id == exact else 0) + sum((10 if term in entity_id else 0)
                    + (8 if term in name or term in aliases else 0)
                    + (8 if term in title else 0) + min(lower.count(term), 4)
                    for term in terms)
        if score:
            _assert_evidence_current(row)
            match = next((lower.find(term) for term in terms if term in lower), 0)
            excerpt = body[max(0, match - 60):match + 240].replace("\n", " ")
            hits.append((score, {"id": entity_id, **row, "sync_review_state": _sync_review_state(),
                                 "warning": _warning(entity_id, row), "excerpt": excerpt}))
    hits.sort(key=lambda item: (-item[0], item[1]["id"]))
    next_offset = offset + limit if offset + limit < len(hits) else None
    return [row | {"total_matches": len(hits), "truncated": next_offset is not None,
                   "next_offset": next_offset}
            for _, row in hits[offset:offset + limit]]


def get_entity(entity_id: str, max_bytes: int = 1_048_576) -> dict:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 1 <= max_bytes <= 4_194_304:
        raise ValueError("Knowledge max_bytes must be 1-4194304")
    entities = _entities()
    entity_id = _resolve_entity(entity_id, entities)
    indexed = entities[entity_id]
    if _inside(indexed["file"], "").stat().st_size > max_bytes:
        raise ValueError("Knowledge note exceeds response byte limit; increase max_bytes")
    row, body = _note(entity_id)
    _assert_evidence_current(row)
    return {"id": entity_id, **row, "sync_review_state": _sync_review_state(),
            "warning": _warning(entity_id, row), "content": body}


def relations(entity_id: str, include_quarantined: bool = False,
              *, direction: str = "both", max_depth: int = 1) -> dict:
    entities = _entities()
    entity_id = _resolve_entity(entity_id, entities)
    _read_indexed_note(entity_id, entities[entity_id])
    _assert_evidence_current(entities[entity_id])
    if direction not in {"both", "incoming", "outgoing"}:
        raise ValueError("Relation direction must be both, incoming, or outgoing")
    if not isinstance(max_depth, int) or not 1 <= max_depth <= 5:
        raise ValueError("Relation max_depth must be 1-5")
    edges = sorted(_json("_INDEX/relations.json")["relations"],
                   key=lambda edge: (edge["from"], edge["to"], edge["type"]))
    if any(edge["from"] not in entities or edge["to"] not in entities for edge in edges):
        raise ValueError("Stale relation index: unknown entity")
    expected_edges = []
    for ident, row in entities.items():
        _read_indexed_note(ident, row)
        for field in RELATION_FIELDS:
            expected_edges.extend({"from": ident, "to": target,
                                   "type": "relates_to" if field == "related_entities" else field}
                                  for target in row.get(field, []))
    order = lambda items: sorted(items, key=lambda edge: (edge["from"], edge["to"], edge["type"]))
    if edges != order(expected_edges):
        raise ValueError("Stale relation index: differs from canonical frontmatter")
    if not include_quarantined:
        edges = [edge for edge in edges if not _quarantined(edge["from"], entities[edge["from"]])
                 and not _quarantined(edge["to"], entities[edge["to"]])]
    result = {"entity_id": entity_id, "warning": _warning(entity_id, entities[entity_id]),
            "authority": entities[entity_id]["authority"],
            "status": entities[entity_id]["status"],
            "outgoing": [{**e, "target_authority": entities[e["to"]]["authority"],
                          "target_status": entities[e["to"]]["status"],
                          "target_warning": _warning(e["to"], entities[e["to"]])}
                         for e in edges if e["from"] == entity_id],
            "incoming": [{**e, "source_authority": entities[e["from"]]["authority"],
                          "source_status": entities[e["from"]]["status"],
                          "source_warning": _warning(e["from"], entities[e["from"]])}
                         for e in edges if e["to"] == entity_id]}
    visited = {entity_id}
    frontier = [entity_id]
    walked = []
    for depth in range(1, max_depth + 1):
        next_frontier = []
        for current in frontier:
            candidates = []
            if direction in {"both", "outgoing"}:
                candidates.extend((edge, edge["to"]) for edge in edges if edge["from"] == current)
            if direction in {"both", "incoming"}:
                candidates.extend((edge, edge["from"]) for edge in edges if edge["to"] == current)
            for edge, neighbor in candidates:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                next_frontier.append(neighbor)
                walked.append({**edge, "depth": depth, "entity_id": neighbor,
                               "authority": entities[neighbor]["authority"],
                               "status": entities[neighbor]["status"],
                               "warning": _warning(neighbor, entities[neighbor])})
        frontier = next_frontier
        if not frontier:
            break
    result["traversal"] = walked
    result["direction"] = direction
    result["max_depth"] = max_depth
    returned_entities = (visited | {edge["to"] for edge in result["outgoing"]}
                         | {edge["from"] for edge in result["incoming"]})
    for ident in sorted(returned_entities):
        _assert_evidence_current(entities[ident])
    return result


def read_algorithm_reference_evidence(reference_id: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Read the local reference; optionally cross-verify the external Engine copy."""
    registry = _reference_registry()
    row = next((item for item in registry["references"] if item["id"] == reference_id), None)
    if row is None:
        raise ValueError("Unknown reference ID")
    data = _local_reference(row)
    external = _external_reference(row)
    start, count = int(start_line), int(line_count)
    if start < 1 or count < 1 or count > 120:
        raise ValueError("Use a positive start and 1-120 lines")
    lines = data.decode("utf-8-sig").splitlines()
    if start > len(lines):
        raise ValueError("Start line exceeds file length")
    end = min(len(lines), start + count - 1)
    return {"reference_id": reference_id, "sha256": row["sha256"], "version": row.get("version"),
            "authority_scope": row.get("authority_scope", "synchronized specification evidence"),
            "source_location": "vault_local",
            "external_verification": "verified" if external is not None else "optional_not_configured",
            "known_invalid_sections": row.get("known_invalid_sections", []),
            "inactive_sections": row.get("inactive_sections", []),
            "narrative_review_status": row.get("narrative_review_status", "not_declared"),
            "semantic_review_entity": row.get("semantic_review_entity"),
            "reference_conflicts": row.get("reference_conflicts", []),
            "warning": "Reference evidence must be interpreted with the current Vault authority model.",
            "start_line": start, "end_line": end,
            "lines": [{"line": n, "text": lines[n - 1]} for n in range(start, end + 1)]}


def get_dataset(entity_id: str) -> dict:
    row, body = _note(entity_id)
    if row["type"] != "data":
        raise ValueError("Expected a dataset entity ID")
    metadata = _frontmatter(body)[0]
    if metadata.get("data_kind") != "dataset":
        raise ValueError("Entity is a retained RAW window; use get_knowledge for its range")
    path = _inside(metadata["raw_path"], "08_DATA/Raw/")
    return {"id": entity_id, "file": row["file"], "status": row["status"],
            "authority": row["authority"], "metadata": metadata,
            "raw_present": path.is_file(), "raw_bytes": path.stat().st_size if path.is_file() else None}


def _iter_json_array(path: Path):
    """Yield array entries without loading the entire RAW file into memory."""
    decoder = strict_json_decoder()
    with path.open("r", encoding="utf-8-sig") as handle:
        buffer = ""
        eof = False

        def refill() -> None:
            nonlocal buffer, eof
            chunk = handle.read(65536)
            if chunk:
                buffer += chunk
            else:
                eof = True

        while not buffer.strip() and not eof:
            refill()
        buffer = buffer.lstrip()
        if not buffer.startswith("["):
            raise ValueError("RAW file must contain a JSON array")
        buffer = buffer[1:]
        first = True
        while True:
            while not buffer.strip() and not eof:
                refill()
            buffer = buffer.lstrip()
            if not first:
                if not buffer and eof:
                    raise ValueError("Incomplete RAW JSON array")
                if buffer.startswith("]"):
                    return
                if not buffer.startswith(","):
                    raise ValueError("Invalid RAW JSON array separator")
                buffer = buffer[1:].lstrip()
            elif buffer.startswith("]"):
                return
            first = False
            while True:
                try:
                    row, end = decoder.raw_decode(buffer)
                    buffer = buffer[end:]
                    yield row
                    break
                except json.JSONDecodeError as exc:
                    if eof:
                        raise ValueError("Malformed RAW JSON row") from exc
                    refill()


def get_window(entity_id: str, *, include_rows: bool = False,
               start_epoch: int | None = None, end_epoch: int | None = None,
               limit: int = 500) -> dict:
    row, body = _note(entity_id)
    if row["type"] != "data":
        raise ValueError("Expected a RAW window entity ID")
    metadata = _frontmatter(body)[0]
    if metadata.get("data_kind") != "window":
        raise ValueError("Entity is not a RAW window")
    path = _inside(metadata["raw_path"], "08_DATA/Raw/")
    result = {"id": entity_id, "file": row["file"], "status": row["status"],
            "authority": row["authority"], "metadata": metadata,
            "data_available": path.is_file(),
            "reason": None if path.is_file() else "vault_raw_unavailable"}
    if not include_rows:
        if start_epoch is not None or end_epoch is not None:
            raise ValueError("A time range requires include_rows=true")
        return result
    start = metadata["first_epoch"] if start_epoch is None else start_epoch
    end = metadata["last_epoch"] if end_epoch is None else end_epoch
    if (not isinstance(start, int) or isinstance(start, bool)
            or not isinstance(end, int) or isinstance(end, bool)
            or not metadata["first_epoch"] <= start <= end <= metadata["last_epoch"]):
        raise ValueError("Invalid time range for registered RAW window")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
        raise ValueError("RAW row limit must be 1-1000")
    if not path.is_file():
        return result | {"rows": [], "truncated": False, "requested_range": [start, end]}
    rows = []
    truncated = False
    for candle in _iter_json_array(path):
        stamp = candle.get("time") if isinstance(candle, dict) else None
        if not isinstance(stamp, int):
            raise ValueError("RAW row has no integer time")
        if stamp < start:
            continue
        if stamp > end:
            break
        if len(rows) == limit:
            truncated = True
            break
        rows.append(candle)
    return result | {"rows": rows, "truncated": truncated,
                     "requested_range": [start, end],
                     "integrity_status": "not_verified_by_window_read"}


def read_evidence(relative: str, start_line: int = 1, line_count: int = 40) -> dict:
    entity = _entities().get(relative)
    if entity is not None:
        if entity.get("type") != "source":
            raise ValueError("Evidence entity must be a source entity")
        fields, _ = _frontmatter(_read_indexed_note(relative, entity))
        relative = fields.get("source_path", "")
    path = _inside(relative, "06_SOURCE/Code/")
    if path.suffix not in {".py", ".js", ".md"} or not path.is_file():
        raise ValueError("Evidence must be a captured source or reference file")
    start = int(start_line)
    count = int(line_count)
    if start < 1 or count < 1 or count > 120:
        raise ValueError("Use a positive start and 1-120 lines")
    manifest = _json("_INDEX/source-hashes.json")
    rows = manifest["files"] + manifest["algorithm_references"] + manifest.get("supporting_files", [])
    pinned = next((r for r in rows if r.get("mirror", r.get("source", r.get("path"))) == relative), None)
    if pinned is None:
        raise ValueError("Evidence file is not pinned in the manifest")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != pinned["sha256"]:
        raise ValueError("Evidence hash differs from the pinned manifest")
    _assert_evidence_current({"source_reference": [relative]})
    if path.suffix == ".md":
        registered = next((row for row in _reference_registry()["references"]
                           if row["local_path"] == relative), None)
        if registered is not None:
            return {**read_algorithm_reference_evidence(registered["id"], start, count),
                    "path": relative, "authority": "documented"}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if start > len(lines):
        raise ValueError("Start line exceeds file length")
    end = min(len(lines), start + count - 1)
    source_row = next((row for entity_id, row in _entities().items()
                       if row.get("type") == "source"
                       and _frontmatter(_read_indexed_note(entity_id, row))[0].get("source_path") == relative), None)
    mixed = bool(source_row and source_row.get("affected_by_known_invalid_order_route"))
    return {"path": relative, "sha256": digest, "authority": "executable",
            "warning": ("Mixed source: dependent regions are known-invalid; an excerpt is not normative approval."
                        if mixed else None), "start_line": start,
            "end_line": end, "lines": [{"line": n, "text": lines[n-1]} for n in range(start, end+1)]}


def verify_package(mode: str = "full-data") -> dict:
    if mode not in {"knowledge", "full-data"}:
        raise ValueError("Verification mode must be knowledge or full-data")
    manifest = _json("_INDEX/source-hashes.json")
    rows = manifest["files"] + manifest["algorithm_references"] + manifest.get("supporting_files", [])
    failures = []
    warnings: list[str] = []
    known_pending: list[str] = []
    entities = _entities()
    try:
        _name_index(entities)
    except (OSError, ValueError, KeyError, TypeError, VaultError) as exc:
        failures.append(f"entity_name_or_content_integrity:{exc}")
    try:
        registry = _reference_registry()
        if not isinstance(registry.get("references"), list):
            raise ValueError("Reference registry has no references list")
        for row in registry["references"]:
            relative = row["repository_relative_path"]
            if (not relative.startswith("engine/algorithms/") or "\\" in relative or ":" in relative
                    or any(part in {"", ".", ".."} for part in relative.split("/"))):
                failures.append(f"unsafe_reference_path:{row['id']}")
    except (OSError, ValueError, KeyError, TypeError, VaultError):
        registry = {"references": []}
        failures.append("reference_registry_invalid")
    indexed_paths = set()
    expected_edges = []
    for entity_id, row in entities.items():
        indexed_paths.add(row["file"])
        try:
            fields, _ = _frontmatter(_read_indexed_note(entity_id, row))
            _assert_evidence_current(fields)
            for field in RELATION_FIELDS:
                for target in fields.get(field, []):
                    expected_edges.append({"from": entity_id,
                                           "type": "relates_to" if field == "related_entities" else field,
                                           "to": target})
        except (OSError, ValueError, KeyError, TypeError, VaultError):
            failures.append(row["file"])
    fixture_errors, fixture_warnings, fixture_known_pending = _fixture_source_review_issues(entities)
    failures.extend(fixture_errors)
    warnings.extend(fixture_warnings)
    known_pending.extend(fixture_known_pending)
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT).as_posix()
        if (any(part in {".git", ".obsidian", "_GENERATED", "Code"} for part in path.relative_to(ROOT).parts)
                or relative.startswith("07_VALIDATION/Fixtures/Sources/") or path.stat().st_size == 0):
            continue
        if relative not in indexed_paths:
            failures.append(relative)
    try:
        edges = _json("_INDEX/relations.json")["relations"]
        ordered = lambda items: sorted(items, key=lambda edge: (edge["from"], edge["type"], edge["to"]))
        if (any(edge["from"] not in entities or edge["to"] not in entities for edge in edges)
                or ordered(edges) != ordered(expected_edges)):
            failures.append("_INDEX/relations.json")
    except (OSError, ValueError, KeyError, TypeError):
        failures.append("_INDEX/relations.json")
    for row in rows:
        relative = row.get("mirror", row.get("source", row.get("path")))
        if mode == "knowledge" and relative.startswith("08_DATA/Raw/"):
            continue
        try:
            path = _inside(relative, "")
            valid = (path.is_file() and path.stat().st_size == row["bytes"]
                     and hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"])
        except (OSError, ValueError, KeyError, TypeError):
            valid = False
        if not valid:
            failures.append(relative)
    pinned_code = {row.get("mirror", row.get("source", row.get("path"))) for row in rows
                   if row.get("mirror", row.get("source", row.get("path"))).startswith("06_SOURCE/Code/")}
    code_root = ROOT / "06_SOURCE/Code"
    if code_root.is_dir():
        for path in code_root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".js", ".md"}:
                relative = path.relative_to(ROOT).as_posix()
                if relative not in pinned_code:
                    failures.append(relative)
    datasets = []
    windows = []
    for entity_id, row in entities.items():
        if row.get("type") != "data":
            continue
        try:
            kind = _frontmatter(_read_indexed_note(entity_id, row))[0].get("data_kind")
            if kind == "dataset":
                datasets.append(entity_id)
            elif kind == "window":
                windows.append(entity_id)
        except (OSError, ValueError, KeyError, TypeError, VaultError):
            continue
    sync_path = ROOT / "_INDEX/sync-status.json"
    sync_status = _json("_INDEX/sync-status.json") if sync_path.is_file() else None
    local_reference_availability = _local_reference_availability(registry, failures)
    reference_availability = _external_reference_availability(registry, failures)
    if mode == "knowledge":
        return {"ok": not failures, "mode": mode, "data_status": "NOT_RUN",
                "verified_pins_ok": not failures and not known_pending, "inventory_complete": None,
                "registered_datasets": len(datasets), "registered_windows": len(windows),
                "verified_evidence": len([row for row in rows if not row.get("mirror", row.get("source", row.get("path"))).startswith("08_DATA/Raw/")]),
                "verified_datasets": 0, "verified_windows": 0, "sync_status": sync_status,
                "local_references": local_reference_availability,
                "external_references": reference_availability, "errors": failures,
                "warnings": warnings, "known_pending": known_pending, "failures": failures}
    registered_raw_files = set()
    for entity_id in datasets:
        try:
            data = get_dataset(entity_id)["metadata"]
            registered_raw_files.add(data["raw_path"])
            path = _inside(data["raw_path"], "08_DATA/Raw/")
            if not path.is_file() or path.stat().st_size != data["raw_bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != data["raw_sha256"]:
                failures.append(data["raw_path"])
        except (OSError, ValueError, KeyError, TypeError):
            failures.append(entity_id)
    candles_by_path = {}
    for entity_id in windows:
        try:
            data = get_window(entity_id)["metadata"]
            path = _inside(data["raw_path"], "08_DATA/Raw/")
        except (OSError, ValueError, KeyError, TypeError):
            failures.append(entity_id)
            continue
        if not path.is_file():
            failures.append(entity_id)
            continue
        try:
            if path not in candles_by_path:
                candles_by_path[path] = strict_json_loads(path.read_bytes())
            candles = candles_by_path[path]
            times = [row["time"] for row in candles]
            start = bisect.bisect_left(times, data["first_epoch"])
            end = bisect.bisect_right(times, data["last_epoch"])
            selected = candles[start:end]
            packed = json.dumps(selected, separators=(",", ":")).encode("utf-8")
            valid = (len(selected) == data["row_count"] and bool(selected)
                     and selected[0]["time"] == data["first_epoch"]
                     and selected[-1]["time"] == data["last_epoch"]
                     and hashlib.sha256(packed).hexdigest() == data["raw_sha256"])
        except (OSError, ValueError, TypeError, KeyError):
            valid = False
        if not valid:
            failures.append(entity_id)
    raw_root = ROOT / "08_DATA/Raw"
    physical_raw_files = {path.relative_to(ROOT).as_posix() for path in raw_root.rglob("*.json")
                          if path.is_file() and not path.name.endswith(".meta.json")} if raw_root.is_dir() else set()
    pinned_sidecars = {row["path"] for row in manifest.get("supporting_files", [])
                       if row["path"].startswith("08_DATA/Raw/") and row["path"].endswith(".meta.json")}
    physical_sidecars = {path.relative_to(ROOT).as_posix() for path in raw_root.rglob("*.meta.json")
                         if path.is_file()} if raw_root.is_dir() else set()
    unregistered_raw_files = sorted(physical_raw_files - registered_raw_files)
    unregistered_raw_sidecars = sorted(physical_sidecars - pinned_sidecars)
    failures.extend(f"unregistered_raw_file:{path}" for path in unregistered_raw_files)
    failures.extend(f"unregistered_raw_sidecar:{path}" for path in unregistered_raw_sidecars)
    inventory_complete = not unregistered_raw_files and not unregistered_raw_sidecars
    ok = not failures
    data_status = ("FAIL" if not ok else "PASS_WITH_WARNINGS" if warnings else
                   "EMPTY_BY_DESIGN" if not datasets and not windows and not physical_raw_files else "PASS")
    return {"ok": ok, "mode": mode, "data_status": data_status,
            "verified_pins_ok": not failures and not known_pending,
            "inventory_complete": inventory_complete,
            "raw_store_status": "EMPTY_BY_DESIGN" if not datasets and not windows and not physical_raw_files else "REGISTERED",
            "fixture_store_status": "EMPTY_BY_DESIGN" if not any(row.get("type") == "case" for row in entities.values()) else "REGISTERED",
            "unregistered_raw_files": unregistered_raw_files,
            "unregistered_raw_sidecars": unregistered_raw_sidecars,
            "verified_evidence": len(rows), "verified_datasets": len(datasets),
            "verified_windows": len(windows), "registered_datasets": len(datasets),
            "registered_windows": len(windows),
            "registered_fixtures": sum(row.get("type") == "case" for row in entities.values()),
            "sync_status": sync_status,
            "local_references": local_reference_availability,
            "external_references": reference_availability, "errors": failures,
            "warnings": warnings, "known_pending": known_pending,
            "failures": failures}
