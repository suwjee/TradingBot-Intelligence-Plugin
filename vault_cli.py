"""Dependency-free command line interface for AI hosts without MCP."""
from __future__ import annotations

import argparse
import json
import sys

import vault_reader as reader


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Read the standalone TradingBot Knowledge Vault")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)
    for command in ("entity", "relations", "dataset", "window"):
        sub.add_parser(command).add_argument("id")
    evidence = sub.add_parser("evidence")
    evidence.add_argument("path")
    evidence.add_argument("--start", type=int, default=1)
    evidence.add_argument("--count", type=int, default=40)
    sub.add_parser("verify")
    args = parser.parse_args()
    try:
        result = {"search": lambda: reader.search(args.query, args.limit),
                  "entity": lambda: reader.get_entity(args.id),
                  "relations": lambda: reader.relations(args.id),
                  "dataset": lambda: reader.get_dataset(args.id),
                  "window": lambda: reader.get_window(args.id),
                  "evidence": lambda: reader.read_evidence(args.path, args.start, args.count),
                  "verify": reader.verify_package}[args.command]()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "verify" and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
