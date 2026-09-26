"""Read-only, Vault-root-relative access to the captured knowledge package."""
from __future__ import annotations

from pathlib import Path
import bisect
import hashlib
import json
import os
import re


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
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
            candidates.append(Path(config["vault_root"]))
        candidates.append(Path(__file__).resolve().parent.parent / "TradingBot-Knowledge")
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        if (root / "_INDEX/entities.json").is_file() and (root / "00_SYSTEM/AUTHORITY_MODEL.md").is_file():
            return root
    raise RuntimeError("Configure the cloned Vault with scripts/configure_vault.py or TRADINGBOT_KNOWLEDGE_VAULT")


ROOT = locate_vault()
INDEX = ROOT / "_INDEX"


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def _inside(relative: str, prefix: str) -> Path:
    if (not isinstance(relative, str) or not relative.startswith(prefix)
            or "\\" in relative or ":" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("Path must be a normalized path inside the Vault")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to((ROOT / prefix).resolve()):
        raise ValueError("Path escapes the Vault")
    return path


def _entities() -> dict:
    return _json("_INDEX/entities.json")["entities"]


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
    return json.loads(data)


def _quarantined(entity_id: str, row: dict) -> bool:
    return entity_id in {"algorithm.order.b", "algorithm.order.c"} or row.get("valid_for_reasoning") is False


def _warning(entity_id: str, row: dict) -> str | None:
    if _quarantined(entity_id, row):
        return "Known-invalid or unresolved knowledge: diagnostic evidence only; do not use for trading reasoning or regression baselines."
    if row.get("affected_by_known_invalid_order_route"):
        return "Mixed source evidence: B/C-dependent regions are known-invalid; assess the cited region before use."
    if row.get("authority") == "non-canonical":
        return "Non-canonical knowledge: inspect status and evidence before use."
    return None


def _frontmatter(content: str) -> tuple[dict, str]:
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
        fields[key] = json.loads(value.strip())
    return fields, body


def _read_indexed_note(entity_id: str, row: dict) -> str:
    content = _inside(row["file"], "").read_text(encoding="utf-8-sig")
    fields, _ = _frontmatter(content)
    expected = {"id": entity_id, **{key: row[key] for key in ("type", "status", "authority", "title")}}
    if any(fields.get(key) != value for key, value in expected.items()):
        raise ValueError(f"Stale entity index: {entity_id}")
    return content


def _sync_review_state() -> str:
    path = ROOT / "_INDEX/sync-status.json"
    if not path.is_file():
        return "snapshot_without_commit_pin"
    return json.loads(path.read_text(encoding="utf-8-sig")).get("review_state", "unknown")


def _note(entity_id: str) -> tuple[dict, str]:
    row = _entities().get(entity_id)
    if row is None:
        raise ValueError(f"Unknown entity: {entity_id}")
    return row, _read_indexed_note(entity_id, row)


def search(query: str, limit: int = 8, include_quarantined: bool = False) -> list[dict]:
    terms = [term.casefold() for term in re.findall(r"\w+", query) if len(term) > 1]
    if not terms:
        raise ValueError("Supply a search term")
    if re.fullmatch(r"order[_ ]?audit", query.strip(), re.IGNORECASE):
        return []
    limit = max(1, min(int(limit), 25))
    hits = []
    for entity_id, row in _entities().items():
        if _quarantined(entity_id, row) and not include_quarantined:
            continue
        note = _read_indexed_note(entity_id, row)
        body = _frontmatter(note)[1]
        title = row["title"].casefold()
        lower = body.casefold()
        score = sum((10 if term in entity_id else 0)
                    + (8 if term in title else 0) + min(lower.count(term), 4)
                    for term in terms)
        if score:
            match = next((lower.find(term) for term in terms if term in lower), 0)
            excerpt = body[max(0, match - 60):match + 240].replace("\n", " ")
            hits.append((score, {"id": entity_id, **row, "sync_review_state": _sync_review_state(),
                                 "warning": _warning(entity_id, row), "excerpt": excerpt}))
    hits.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [row for _, row in hits[:limit]]


def get_entity(entity_id: str) -> dict:
    row, body = _note(entity_id)
    return {"id": entity_id, **row, "sync_review_state": _sync_review_state(),
            "warning": _warning(entity_id, row), "content": body}


def relations(entity_id: str, include_quarantined: bool = False) -> dict:
    entities = _entities()
    if entity_id not in entities:
        raise ValueError(f"Unknown entity: {entity_id}")
    edges = _json("_INDEX/relations.json")["relations"]
    if not include_quarantined:
        edges = [edge for edge in edges if not _quarantined(edge["from"], entities[edge["from"]])
                 and not _quarantined(edge["to"], entities[edge["to"]])]
    return {"entity_id": entity_id, "warning": _warning(entity_id, entities[entity_id]),
            "authority": entities[entity_id]["authority"],
            "outgoing": [{**e, "target_authority": entities[e["to"]]["authority"],
                          "target_warning": _warning(e["to"], entities[e["to"]])}
                         for e in edges if e["from"] == entity_id],
            "incoming": [{**e, "source_authority": entities[e["from"]]["authority"],
                          "source_warning": _warning(e["from"], entities[e["from"]])}
                         for e in edges if e["to"] == entity_id]}


def read_algorithm_reference_evidence(reference_id: str, start_line: int = 1, line_count: int = 40) -> dict:
    """Read an optional, hash-verified production reference without making it a Vault dependency."""
    registry = _reference_registry()
    row = next((item for item in registry["references"] if item["id"] == reference_id), None)
    if row is None:
        raise ValueError("Unknown reference ID")
    configured = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    if not configured:
        raise ValueError("Set TRADINGBOT_ENGINE_ROOT to the TradingBot repository root for optional reference evidence")
    relative = row["repository_relative_path"]
    if (not relative.startswith("engine/algorithms/") or "\\" in relative or ":" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError("Unsafe reference registry path")
    root = Path(configured).expanduser().resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to((root / "engine/algorithms").resolve()) or not path.is_file():
        raise ValueError("Configured reference file is unavailable")
    data = path.read_bytes()
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("External reference identity differs from the pinned registry")
    start, count = int(start_line), int(line_count)
    if start < 1 or count < 1 or count > 120:
        raise ValueError("Use a positive start and 1-120 lines")
    lines = data.decode("utf-8-sig").splitlines()
    if start > len(lines):
        raise ValueError("Start line exceeds file length")
    end = min(len(lines), start + count - 1)
    return {"reference_id": reference_id, "sha256": row["sha256"], "version": row["version"],
            "authority_scope": row["authority_scope"], "known_invalid_sections": row["known_invalid_sections"],
            "inactive_sections": row["inactive_sections"],
            "warning": "Reference evidence is descriptive; current Order_B/C semantics are known-invalid and audit is inactive.",
            "start_line": start, "end_line": end,
            "lines": [{"line": n, "text": lines[n - 1]} for n in range(start, end + 1)]}


def get_dataset(entity_id: str) -> dict:
    row, body = _note(entity_id)
    if not re.fullmatch(r"data\.dataset_[0-9a-f]{8}", entity_id) or row["type"] != "data":
        raise ValueError("Expected a dataset entity ID")
    metadata = _frontmatter(body)[0]
    if metadata.get("data_kind") != "dataset":
        raise ValueError("Entity is a retained RAW window; use get_knowledge for its range")
    path = _inside(metadata["raw_path"], "08_DATA/Raw/")
    return {"id": entity_id, "file": row["file"], "status": row["status"],
            "authority": row["authority"], "metadata": metadata,
            "raw_present": path.is_file(), "raw_bytes": path.stat().st_size if path.is_file() else None}


def get_window(entity_id: str) -> dict:
    row, body = _note(entity_id)
    if not re.fullmatch(r"data\.window_[0-9a-f]{8}", entity_id) or row["type"] != "data":
        raise ValueError("Expected a RAW window entity ID")
    metadata = _frontmatter(body)[0]
    if metadata.get("data_kind") != "window":
        raise ValueError("Entity is not a RAW window")
    path = _inside(metadata["raw_path"], "08_DATA/Raw/")
    return {"id": entity_id, "file": row["file"], "status": row["status"],
            "authority": row["authority"], "metadata": metadata,
            "data_available": path.is_file(),
            "reason": None if path.is_file() else "vault_raw_unavailable"}


def read_evidence(relative: str, start_line: int = 1, line_count: int = 40) -> dict:
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
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if start > len(lines):
        raise ValueError("Start line exceeds file length")
    end = min(len(lines), start + count - 1)
    mixed = relative in {
        "06_SOURCE/Code/engine/pipeline/e_zone_detector.py",
        "06_SOURCE/Code/engine/pipeline/lifecycle_engine.py",
        "06_SOURCE/Code/engine/bridge/trading_pipeline.py",
    }
    return {"path": relative, "sha256": digest, "authority": "executable",
            "warning": ("Mixed source: current Order_B/C-dependent regions are known-invalid; an excerpt is not normative approval."
                        if mixed else None), "start_line": start,
            "end_line": end, "lines": [{"line": n, "text": lines[n-1]} for n in range(start, end+1)]}


def verify_package(mode: str = "full-data") -> dict:
    if mode not in {"knowledge", "full-data"}:
        raise ValueError("Verification mode must be knowledge or full-data")
    manifest = _json("_INDEX/source-hashes.json")
    rows = manifest["files"] + manifest["algorithm_references"] + manifest.get("supporting_files", [])
    failures = []
    entities = _entities()
    if "algorithm.orderaudit" in entities:
        failures.append("inactive_order_audit_entity")
    for entity_id in ("algorithm.order.b", "algorithm.order.c"):
        row = entities.get(entity_id, {})
        if row.get("status") != "pending-fix" or row.get("authority") != "non-canonical" or row.get("valid_for_reasoning") is not False:
            failures.append(f"quarantine_metadata:{entity_id}")
    try:
        registry = _reference_registry()
        if {row["id"] for row in registry["references"]} != {"bullish_hpzr6", "bearish_hpzr6"}:
            failures.append("reference_registry_incomplete")
        for row in registry["references"]:
            relative = row["repository_relative_path"]
            if (not relative.startswith("engine/algorithms/") or "\\" in relative or ":" in relative
                    or any(part in {"", ".", ".."} for part in relative.split("/"))):
                failures.append(f"unsafe_reference_path:{row['id']}")
    except (OSError, ValueError, KeyError, TypeError):
        registry = {"references": []}
        failures.append("reference_registry_invalid")
    indexed_paths = set()
    for entity_id, row in entities.items():
        indexed_paths.add(row["file"])
        try:
            _read_indexed_note(entity_id, row)
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            failures.append(row["file"])
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT).as_posix()
        if (any(part in {".git", ".obsidian", "Code"} for part in path.relative_to(ROOT).parts)
                or relative.startswith("07_VALIDATION/Fixtures/Sources/") or path.stat().st_size == 0):
            continue
        if relative not in indexed_paths:
            failures.append(relative)
    try:
        edges = _json("_INDEX/relations.json")["relations"]
        if any(edge["from"] not in entities or edge["to"] not in entities for edge in edges):
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
    required_engine = {f"06_SOURCE/Code/engine/pipeline/{name}.py" for name in (
        "reaction_engine", "blue_line_detector", "a_zone_detector", "s_zone_detector",
        "e_zone_detector", "lifecycle_engine", "direction_policy", "core_utils")}
    required_engine.add("06_SOURCE/Code/engine/bridge/trading_pipeline.py")
    if not required_engine.issubset(pinned_code):
        failures.append("incomplete_engine_source_coverage")
    if code_root.is_dir():
        for path in code_root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".js", ".md"}:
                relative = path.relative_to(ROOT).as_posix()
                if relative not in pinned_code:
                    failures.append(relative)
    datasets = [entity_id for entity_id in entities
                if re.fullmatch(r"data\.dataset_[0-9a-f]{8}", entity_id)]
    windows = [entity_id for entity_id in entities
               if re.fullmatch(r"data\.window_[0-9a-f]{8}", entity_id)]
    sync_path = ROOT / "_INDEX/sync-status.json"
    sync_status = json.loads(sync_path.read_text(encoding="utf-8-sig")) if sync_path.is_file() else None
    if mode == "knowledge":
        return {"ok": not failures, "mode": mode, "data_status": "NOT_RUN",
                "verified_pins_ok": not failures, "inventory_complete": None,
                "registered_datasets": len(datasets), "registered_windows": len(windows),
                "verified_evidence": len([row for row in rows if not row.get("mirror", row.get("source", row.get("path"))).startswith("08_DATA/Raw/")]),
                "verified_datasets": 0, "verified_windows": 0, "sync_status": sync_status,
                "failures": failures}
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
                candles_by_path[path] = json.loads(path.read_bytes())
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
    inventory_complete = not unregistered_raw_files and not unregistered_raw_sidecars
    reference_availability = {}
    configured_engine = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    for item in registry["references"]:
        if not configured_engine:
            reference_availability[item["id"]] = "optional_not_configured"
            continue
        try:
            root = Path(configured_engine).expanduser().resolve()
            path = (root / item["repository_relative_path"]).resolve()
            if not path.is_relative_to((root / "engine/algorithms").resolve()):
                raise ValueError("Reference path escapes configured algorithms root")
            data = path.read_bytes()
            valid = len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
            reference_availability[item["id"]] = "verified" if valid else "identity_mismatch"
            if not valid:
                failures.append(f"reference_identity:{item['id']}")
        except (OSError, ValueError, KeyError):
            reference_availability[item["id"]] = "unavailable"
            failures.append(f"reference_unavailable:{item['id']}")
    return {"ok": not failures and inventory_complete, "mode": mode,
            "data_status": "PASS" if not failures and inventory_complete else "FAIL",
            "verified_pins_ok": not failures,
            "inventory_complete": inventory_complete,
            "unregistered_raw_files": unregistered_raw_files,
            "unregistered_raw_sidecars": unregistered_raw_sidecars,
            "verified_evidence": len(rows), "verified_datasets": len(datasets),
            "verified_windows": len(windows), "sync_status": sync_status,
            "external_references": reference_availability,
            "failures": failures}
