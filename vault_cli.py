"""Command line knowledge interface for AI hosts without MCP transport."""
from __future__ import annotations

import argparse
import json
import sys

import vault_reader as reader


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Read the standalone TradingBot Knowledge Vault")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--offset", type=int, default=0)
    search.add_argument("--include-quarantined", action="store_true")
    search.add_argument("--include-noncanonical", action="store_true")
    search.add_argument("--include-pending", action="store_true")
    search.add_argument("--type", dest="entity_type")
    search.add_argument("--authority")
    search.add_argument("--status")
    for command in ("entity", "relations", "dataset", "window"):
        sub.add_parser(command).add_argument("id")
    sub.choices["entity"].add_argument("--max-bytes", type=int, default=1_048_576)
    sub.choices["relations"].add_argument("--include-quarantined", action="store_true")
    sub.choices["relations"].add_argument("--direction", choices=("both", "incoming", "outgoing"), default="both")
    sub.choices["relations"].add_argument("--max-depth", type=int, default=1)
    sub.choices["window"].add_argument("--include-rows", action="store_true")
    sub.choices["window"].add_argument("--start-epoch", type=int)
    sub.choices["window"].add_argument("--end-epoch", type=int)
    sub.choices["window"].add_argument("--limit", type=int, default=500)
    evidence = sub.add_parser("evidence")
    evidence.add_argument("path")
    evidence.add_argument("--start", type=int, default=1)
    evidence.add_argument("--count", type=int, default=40)
    reference = sub.add_parser("reference-evidence")
    reference.add_argument("id")
    reference.add_argument("--start", type=int, default=1)
    reference.add_argument("--count", type=int, default=40)
    verify = sub.add_parser("verify")
    verify.add_argument("--mode", choices=("knowledge", "full-data"), default="full-data")
    sub.add_parser("doctor")
    args = parser.parse_args()
    try:
        result = {"search": lambda: reader.search(args.query, args.limit, args.include_quarantined,
                                                    entity_type=args.entity_type, authority=args.authority,
                                                    status=args.status, include_noncanonical=args.include_noncanonical,
                                                    include_pending=args.include_pending, offset=args.offset),
                  "entity": lambda: reader.get_entity(args.id, args.max_bytes),
                  "relations": lambda: reader.relations(args.id, args.include_quarantined,
                                                         direction=args.direction, max_depth=args.max_depth),
                  "dataset": lambda: reader.get_dataset(args.id),
                  "window": lambda: reader.get_window(args.id, include_rows=args.include_rows,
                                                       start_epoch=args.start_epoch, end_epoch=args.end_epoch,
                                                       limit=args.limit),
                  "evidence": lambda: reader.read_evidence(args.path, args.start, args.count),
                  "reference-evidence": lambda: reader.read_algorithm_reference_evidence(args.id, args.start, args.count),
                  "verify": lambda: reader.verify_package(args.mode),
                  "doctor": lambda: __import__("runtime_doctor").doctor()}[args.command]()
    except (ValueError, OSError, KeyError, reader.VaultError) as exc:
        print(json.dumps(reader.error_payload(exc), ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "verify" and not result["ok"]:
        return 1
    if args.command == "doctor" and not result["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
