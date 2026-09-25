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


def search(query: str, limit: int = 8) -> list[dict]:
    terms = [term.casefold() for term in re.findall(r"\w+", query) if len(term) > 1]
    if not terms:
        raise ValueError("Supply a search term")
    limit = max(1, min(int(limit), 25))
    hits = []
    for entity_id, row in _entities().items():
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
            hits.append((score, {"id": entity_id, **row, "sync_review_state": _sync_review_state(), "excerpt": excerpt}))
    hits.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [row for _, row in hits[:limit]]


def get_entity(entity_id: str) -> dict:
    row, body = _note(entity_id)
    return {"id": entity_id, **row, "sync_review_state": _sync_review_state(), "content": body}


def relations(entity_id: str) -> dict:
    if entity_id not in _entities():
        raise ValueError(f"Unknown entity: {entity_id}")
    edges = _json("_INDEX/relations.json")["relations"]
    return {"entity_id": entity_id,
            "outgoing": [e for e in edges if e["from"] == entity_id],
            "incoming": [e for e in edges if e["to"] == entity_id]}


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
    _inside(metadata["raw_path"], "08_DATA/Raw/")
    return {"id": entity_id, "file": row["file"], "status": row["status"],
            "authority": row["authority"], "metadata": metadata}


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
    return {"path": relative, "sha256": digest, "start_line": start,
            "end_line": end, "lines": [{"line": n, "text": lines[n-1]} for n in range(start, end+1)]}


def verify_package() -> dict:
    manifest = _json("_INDEX/source-hashes.json")
    rows = manifest["files"] + manifest["algorithm_references"] + manifest.get("supporting_files", [])
    failures = []
    entities = _entities()
    if not manifest["algorithm_references"] and any(
        row["authority"] == "normative" and row["type"] in {"core", "market", "behavior", "algorithm", "mirror"}
        for row in entities.values()
    ):
        failures.append("normative_trading_rule_without_reference")
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
    datasets = [entity_id for entity_id in entities
                if re.fullmatch(r"data\.dataset_[0-9a-f]{8}", entity_id)]
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
    windows = [entity_id for entity_id in entities
               if re.fullmatch(r"data\.window_[0-9a-f]{8}", entity_id)]
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
    sync_path = ROOT / "_INDEX/sync-status.json"
    sync_status = json.loads(sync_path.read_text(encoding="utf-8-sig")) if sync_path.is_file() else None
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
    return {"ok": not failures and inventory_complete, "verified_pins_ok": not failures,
            "inventory_complete": inventory_complete,
            "unregistered_raw_files": unregistered_raw_files,
            "unregistered_raw_sidecars": unregistered_raw_sidecars,
            "verified_evidence": len(rows), "verified_datasets": len(datasets),
            "verified_windows": len(windows), "sync_status": sync_status,
            "failures": failures}
