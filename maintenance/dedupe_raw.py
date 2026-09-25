"""One-time, source-verified consolidation of three exact RAW windows."""
from __future__ import annotations

import bisect
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "TradingBot-Knowledge"
RAW = ROOT / "08_DATA/Raw/XAUUSD"
MAPPING = {
    "0291455b": "f531a06d",
    "18632e27": "ea82be1a",
    "d33c7e2c": "ea82be1a",
}


def parse_note(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    header, body = text[4:].split("\n---\n", 1)
    return {key: json.loads(value) for line in header.splitlines()
            for key, value in [line.split(": ", 1)]}, body


def save_note(path: Path, fields: dict, body: str) -> None:
    header = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                       for key, value in fields.items())
    path.write_text(f"---\n{header}\n---\n{body}", encoding="utf-8")


def main() -> None:
    notes = ROOT / "08_DATA/Datasets"
    records = {}
    for small_id, large_id in MAPPING.items():
        small_note = notes / f"Dataset-{small_id}.md"
        large_note = notes / f"Dataset-{large_id}.md"
        small, small_body = parse_note(small_note)
        large, large_body = parse_note(large_note)
        small_path = ROOT / small["raw_path"]
        large_path = ROOT / large["raw_path"]
        assert small_path.is_file() and large_path.is_file()
        assert small_path.resolve().is_relative_to(RAW.resolve())
        assert large_path.resolve().is_relative_to(RAW.resolve())
        assert hashlib.sha256(small_path.read_bytes()).hexdigest() == small["raw_sha256"]
        assert hashlib.sha256(large_path.read_bytes()).hexdigest() == large["raw_sha256"]
        parent = json.loads(large_path.read_bytes())
        times = [row["time"] for row in parent]
        start = bisect.bisect_left(times, small["first_epoch"])
        end = bisect.bisect_right(times, small["last_epoch"])
        window = parent[start:end]
        packed = json.dumps(window, separators=(",", ":")).encode("utf-8")
        assert len(window) == small["row_count"]
        assert hashlib.sha256(packed).hexdigest() == small["raw_sha256"]
        records[small_id] = (small, small_body, large, large_body, small_path, large_path)

    # All three windows were checked before any write. Preserve their original
    # hashes as verifiable window identities; only the parent is a physical RAW.
    for small_id, (small, _body, large, _large_body, _small_path, _large_path) in records.items():
        large_id = MAPPING[small_id]
        path = notes / f"Dataset-{large_id}.md"
        large, large_body = parse_note(path)
        large["used_by_fixtures"] = sorted(set(large["used_by_fixtures"] + small["used_by_fixtures"]))
        large["produces_behaviors"] = sorted(set(large["produces_behaviors"] + small["produces_behaviors"]))
        large["related_entities"] = sorted(set(large["related_entities"] + small["used_by_fixtures"] + small["produces_behaviors"]))
        save_note(path, large, large_body)

        original_hash = small["raw_sha256"]
        original_bytes = small["raw_bytes"]
        for key in ("name", "raw_locations", "raw_bytes"):
            small.pop(key, None)
        small["id"] = f"data.window_{small_id}"
        small["data_kind"] = "window"
        small["title"] = f"Verified RAW window {small_id}"
        small["raw_path"] = large["raw_path"]
        small["retained_raw_sha256"] = large["raw_sha256"]
        small["parent_dataset"] = f"data.dataset_{large_id}"
        small["original_raw_bytes"] = original_bytes
        small["related_entities"] = sorted(set(small["related_entities"] + [small["parent_dataset"]]))
        body = (f"\n# Verified RAW window {small_id}\n\n"
                f"The original {small['row_count']}-candle RAW is now represented by the exact inclusive window "
                f"from epoch `{small['first_epoch']}` through `{small['last_epoch']}` in "
                f"`{large['raw_path']}`. The slice, serialized as compact JSON, has SHA-256 "
                f"`{original_hash}` and matches the removed RAW byte for byte. The retained parent "
                f"has SHA-256 `{large['raw_sha256']}`. A consumer must apply this window before "
                "calculating a fixture that previously used the smaller file; using the whole parent "
                "changes chronology and physical indexes.\n")
        new_path = notes / f"Window-{small_id}.md"
        save_note(new_path, small, body)
        (notes / f"Dataset-{small_id}.md").unlink()

    # Update all fixture pins and retain the exact old input interval.
    for path in (ROOT / "07_VALIDATION/Fixtures").rglob("Fixture-*.md"):
        fields, body = parse_note(path)
        match = next(((small_id, value) for small_id, value in records.items()
                      if fields.get("dataset_sha256") == value[0]["raw_sha256"]), None)
        if match is None:
            continue
        small_id, (small, _small_body, large, _large_body, _small_path, _large_path) = match
        fields["dataset"] = large["raw_path"]
        fields["dataset_sha256"] = large["raw_sha256"]
        fields["dataset_window_first_epoch"] = small["first_epoch"]
        fields["dataset_window_last_epoch"] = small["last_epoch"]
        fields["dataset_window_row_count"] = small["row_count"]
        fields["dataset_window_sha256"] = small["raw_sha256"]
        fields["related_entities"] = sorted(set(fields["related_entities"] + [f"data.window_{small_id}"]))
        body += (f"\n## Reproduction RAW window\n\nUse `{large['raw_path']}` and select the "
                 f"inclusive source-row interval `{small['first_epoch']}`–`{small['last_epoch']}`. "
                 f"The resulting {small['row_count']} rows reproduce SHA-256 `{small['raw_sha256']}` "
                 "for the former small RAW. Do not calculate from the entire parent for this case.\n")
        save_note(path, fields, body)

    # The source fixture and captured references are immutable evidence. Current
    # navigation notes can instead point to the retained RAW and window entity.
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(("06_SOURCE/Code/", "07_VALIDATION/Fixtures/Sources/", "00_SYSTEM/")):
            continue
        text = path.read_text(encoding="utf-8-sig")
        for small_id, (small, _body, large, _large_body, _small_path, _large_path) in records.items():
            if f"Window-{small_id}.md" not in rel:
                text = text.replace(_small_path.relative_to(ROOT).as_posix(), large["raw_path"])
            text = text.replace(f"data.dataset_{small_id}", f"data.window_{small_id}")
            text = text.replace(f"Dataset-{small_id}.md", f"Window-{small_id}.md")
        if text != path.read_text(encoding="utf-8-sig"):
            path.write_text(text, encoding="utf-8")

    manifest_path = ROOT / "_INDEX/source-hashes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    removed_sidecars = {_small_path.relative_to(ROOT).as_posix() + ".meta.json"
                        for _small, _body, _large, _large_body, _small_path, _large_path in records.values()}
    manifest["supporting_files"] = [row for row in manifest["supporting_files"]
                                    if row["path"] not in removed_sidecars]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for small_id, (small, *_rest) in records.items():
        print(f"MIGRATED {small_id} -> {MAPPING[small_id]}: {small['first_epoch']}..{small['last_epoch']}")
    print("Raw files and sidecars still present; remove only after index validation.")


if __name__ == "__main__":
    main()
