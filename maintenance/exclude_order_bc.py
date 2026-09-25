"""Remove superseded Order B/C knowledge from the standalone Vault.

Original mixed source/reference files are retained in the separate excluded
archive. The Vault keeps only its source evidence that has no B/C code.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re

VAULT = Path(__file__).resolve().parents[2] / "TradingBot-Knowledge"
EXCLUDED = VAULT.parent / "TradingBot-Knowledge-Excluded"
EXCLUDED_IDS = {
    "algorithm.order.b", "algorithm.order.c",
    "case.fixture_1_2", "case.fixture_1_3", "case.fixture_2_1",
    "case.fixture_2_2", "case.fixture_4_2", "case.fixture_5_3",
    "system.executed_phases_audit", "system.phase_4_5_audit",
}
EXCLUDED_SOURCE_PATHS = {
    "06_SOURCE/Code/engine/bridge/trading_pipeline.py",
    "06_SOURCE/Code/engine/pipeline/e_zone_detector.py",
    "06_SOURCE/Code/engine/pipeline/lifecycle_engine.py",
}
EXCLUDED_SOURCE_IDS = {
    "source.trading_pipeline", "source.e_zone_detector", "source.lifecycle_engine",
}
EXCLUDED_CASES = {"1.2", "1.3", "2.1", "2.2", "4.2", "5.3"}
EXCLUDED_HISTORY = {"8.5", "8.6", "8.7"}
ORDER_PATTERN = re.compile(r"\b(?:Order[_ -]?[BC]|order_[bc]|algorithm\.order\.[bc])\b", re.I)


def parse(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8-sig")
    head, body = raw[4:].split("\n---\n", 1)
    return {key: json.loads(value) for line in head.splitlines()
            for key, value in [line.split(": ", 1)]}, body


def write(path: Path, fields: dict, body: str) -> None:
    head = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                     for key, value in fields.items())
    path.write_text(f"---\n{head}\n---\n{body}", encoding="utf-8")


def curated_fixture(source: Path) -> tuple[str, dict[str, int]]:
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    kept: list[str] = []
    skip = False
    for line in lines:
        case = re.match(r"^### ([1-6]\.[0-9]+)\b", line)
        history = re.match(r"^### (8\.[0-9]+)\b", line)
        if line.startswith("## ") or case or history:
            skip = bool((case and case.group(1) in EXCLUDED_CASES)
                        or (history and history.group(1) in EXCLUDED_HISTORY))
        if not skip and not ORDER_PATTERN.search(line):
            kept.append(line)
    title = ["# Curated retained fixture anchors", "",
             "This Vault-local copy excludes the superseded physical Order routes and their dependent cases.",
             "The original mixed document is outside this Vault. Remaining assertions retain their section IDs,",
             "but their source hash and line anchors refer to this curated copy only.", ""]
    rendered = "\n".join(title + kept).rstrip() + "\n"
    headings = {match.group(1): number for number, line in enumerate(rendered.splitlines(), 1)
                if (match := re.match(r"^### ([1-8]\.[0-9]+)\b", line))}
    return rendered, headings


def main() -> None:
    assert VAULT.is_dir() and EXCLUDED.is_dir()
    fixture = VAULT / "07_VALIDATION/Fixtures/Sources/TradingBot_Fixtures_Regression_Anchors.md"
    original = EXCLUDED / "07_VALIDATION/Fixtures/Sources/TradingBot_Fixtures_Regression_Anchors.md"
    if not original.is_file():
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(fixture.read_bytes())
    curated, headings = curated_fixture(original)
    fixture.write_text(curated, encoding="utf-8")
    fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()

    manifest_path = VAULT / "_INDEX/source-hashes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest["files"] = [row for row in manifest["files"]
                         if row["source"] not in EXCLUDED_SOURCE_PATHS]
    manifest["algorithm_references"] = []
    for row in manifest["supporting_files"]:
        if row["path"] == fixture.relative_to(VAULT).as_posix():
            row["sha256"] = fixture_hash
            row["bytes"] = fixture.stat().st_size
    manifest["mirror_kind"] = "byte-exact retained source subset"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Keep ID continuity for mixed source owners without retaining their code.
    pending = VAULT / "06_SOURCE/Pending"
    pending.mkdir(exist_ok=True)
    for ident in sorted(EXCLUDED_SOURCE_IDS):
        path = pending / (ident.split(".", 1)[1] + ".md")
        fields = {"id": ident, "type": "source", "status": "pending",
                  "authority": "non-canonical", "title": "Source evidence pending rewrite",
                  "related_entities": [], "source_reference": []}
        write(path, fields, "\n# Source evidence pending rewrite\n\nThe mixed source snapshot was excluded from this Vault. No implementation claim is made here.\n")

    notes: dict[str, tuple[Path, dict, str]] = {}
    for path in VAULT.rglob("*.md"):
        rel = path.relative_to(VAULT).as_posix()
        if (path.stat().st_size == 0 or rel.startswith("06_SOURCE/Code/")
                or rel.startswith("07_VALIDATION/Fixtures/Sources/")
                or ".obsidian" in path.parts):
            continue
        fields, body = parse(path)
        notes[fields["id"]] = (path, fields, body)

    for ident, (path, fields, body) in notes.items():
        if ident in EXCLUDED_SOURCE_IDS:
            continue
        for key, value in list(fields.items()):
            if key in {"source_refs", "source_reference"}:
                fields[key] = [ref for ref in value if ref.split("#L", 1)[0] not in EXCLUDED_SOURCE_PATHS
                               and "/algorithms/TradingBot_" not in ref]
            elif key in {"implemented_by", "calculated_by", "depends_on", "produces",
                         "implements", "affects", "parent_of", "child_of", "relates_to",
                         "supports", "orchestrates", "related_entities", "used_by_fixtures"}:
                fields[key] = [target for target in value if target not in EXCLUDED_IDS]
            elif key == "external_source_paths":
                fields[key] = [ref for ref in value if ref not in EXCLUDED_SOURCE_PATHS]
            elif key == "external_source_hashes":
                fields[key] = {ref: hash_value for ref, hash_value in value.items()
                               if ref not in EXCLUDED_SOURCE_PATHS}
        if fields.get("type") == "case":
            section = re.fullmatch(r"case\.fixture_([0-9]+)_([0-9]+)", ident)
            key = f"{section.group(1)}.{section.group(2)}" if section else ""
            if key not in headings:
                raise ValueError(f"Retained fixture heading missing: {ident}")
            fields["source_fixture_line"] = headings[key]
            fields["source_fixture_sha256"] = fixture_hash
            if fields["source_module"] in EXCLUDED_SOURCE_PATHS:
                fields["source_module"] = "unknown"
                fields["source_function"] = "unknown"
                if fields["fixture_status"] == "Active":
                    fields["fixture_status"] = "Pending"
                    fields["fixture_authority"] = "Pending"
                    fields["status"] = "draft"
                    fields["authority"] = "non-canonical"
        if fields.get("id") == "algorithm.order.a":
            fields["implemented_by"] = ["source.s_zone_detector"]
            fields["depends_on"] = ["algorithm.order", "algorithm.a"]
            fields["status"] = "active"
            fields["authority"] = "empirical"
            body = "\n# Order_A parent-stop cause\n\nThe retained S-stage source selects the first canonical opposite Reaction after an eligible A strict stop, ordered by exact confirmation and physical indexes. This first physical Order_A owner remains fixed while S is undecided. Other routes await a new source-grounded review.\n"
        if fields.get("id") == "algorithm.order":
            fields["implemented_by"] = ["source.reaction_engine", "source.s_zone_detector"]
            body = "\n# Physical Order identity\n\nA physical Order is a canonical opposite Reaction with identity `(FirstIndex,BreakIndex)`. The retained Order creation route in this Vault is `Order_A` after an eligible parent stop. Native Reaction modes A and B are separate state-machine labels. Additional creation routes are outside the current Vault authority.\n"
        # The pending source entities still satisfy structural owner links, but
        # dependent algorithm/behavior claims must not be normative.
        if fields.get("type") in {"algorithm", "behavior"} and any(
                owner in EXCLUDED_SOURCE_IDS for owner in fields.get("implemented_by", [])):
            fields["status"] = "pending-fix" if ident == "algorithm.orderaudit" else "pending"
            fields["authority"] = "non-canonical"
        if (fields.get("type") != "system" and not fields.get("source_reference")
                and fields.get("authority") in {"normative", "executable", "canonical"}):
            fields["status"] = "pending"
            fields["authority"] = "non-canonical"
        filtered = []
        for line in body.splitlines():
            if ORDER_PATTERN.search(line):
                continue
            if ("S/Type-3.md" not in path.as_posix()
                    and "Behavior-Mirror.md" not in path.as_posix()
                    and ("reset-leg" in line.lower() or "blue-leg" in line.lower()
                         or "Order_A/B/C" in line)):
                continue
            if any(path_text in line for path_text in EXCLUDED_SOURCE_PATHS):
                continue
            if "/algorithms/TradingBot_" in line:
                continue
            if any(f"Fixture-{case.replace('.', '-')}.md" in line for case in EXCLUDED_CASES):
                continue
            filtered.append(line)
        write(path, fields, "\n".join(filtered).rstrip() + "\n")

    # Reconstruct inverse source links for surviving algorithm owner relations.
    for ident in EXCLUDED_SOURCE_IDS:
        path = pending / (ident.split(".", 1)[1] + ".md")
        fields, body = parse(path)
        fields["implements"] = sorted(note_id for note_id, (_path, note, _body) in notes.items()
                                      if note.get("type") == "algorithm" and ident in note.get("implemented_by", []))
        write(path, fields, body)
    # A normative dependency on pending knowledge would silently promote a
    # missing implementation. Downgrade the dependent claim until it is rebuilt.
    note_fields = {ident: parse(path)[0] for ident, (path, _fields, _body) in notes.items()}
    note_fields.update({ident: parse(pending / (ident.split(".", 1)[1] + ".md"))[0]
                        for ident in EXCLUDED_SOURCE_IDS})
    changed = True
    while changed:
        changed = False
        for ident, fields in note_fields.items():
            if fields["authority"] != "normative":
                continue
            for key in ("calculated_by", "implemented_by", "depends_on", "produces",
                        "implements", "supports", "orchestrates", "parent_of", "child_of"):
                if any(note_fields.get(target, {}).get("authority") == "non-canonical"
                       for target in fields.get(key, [])):
                    fields["status"] = "pending-fix" if ident == "algorithm.orderaudit" else "pending"
                    fields["authority"] = "non-canonical"
                    changed = True
                    break
    for ident, (path, _fields, _body) in notes.items():
        fields, body = parse(path)
        if fields["authority"] != note_fields[ident]["authority"]:
            fields["status"] = note_fields[ident]["status"]
            fields["authority"] = note_fields[ident]["authority"]
            write(path, fields, body)
    print(f"Curated fixture SHA-256: {fixture_hash}; retained case headings: {len(headings)}")


if __name__ == "__main__":
    main()
