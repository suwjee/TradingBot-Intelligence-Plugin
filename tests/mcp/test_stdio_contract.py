"""Exercise all public tools through the declared MCP stdio launcher."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from tests.helpers.mcp_client import run_mcp_session
from tests.helpers.real_roots import require_real_roots
from tests.helpers.snapshots import assert_unchanged, snapshot_files
from tests.integration.test_real_vault import load_index
from tests.helpers.fake_vault import EntitySpec, build_fake_vault


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TOOLS = {"search_knowledge", "get_knowledge", "trace_relations", "get_dataset",
         "get_raw_window", "read_source_evidence", "read_algorithm_reference_evidence",
         "verify_vault"}


def payloads(result):
    """Decode public text payloads without discarding protocol error markers."""
    return [json.loads(item.text) for item in result.content if getattr(item, "text", None)]


class StdioContractTests(unittest.TestCase):
    def test_configured_external_source_mismatch_is_structured_for_knowledge_and_both_excerpt_routes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary)
            vault,engine=base / "vault",base / "engine"
            path="06_SOURCE/Code/engine/pipeline/sample.py"
            source=EntitySpec("source.sample","06_SOURCE/sample.md","source","active","executable",
                              "Synthetic source","Software transport evidence only.",{"source_path":path})
            build_fake_vault(vault,[source],source_files={path:b"VALUE = 1\n"})
            external=engine / "engine/pipeline/sample.py"
            external.parent.mkdir(parents=True)
            external.write_bytes(b"VALUE = 2\n")
            environment=os.environ.copy()
            environment.update(TRADINGBOT_KNOWLEDGE_VAULT=str(vault),TRADINGBOT_ENGINE_ROOT=str(engine),
                               TRADINGBOT_PLUGIN_PYTHON=sys.executable,PYTHONDONTWRITEBYTECODE="1")
            calls={"get_knowledge":{"entity_id":"source.sample"},
                   "read_source_evidence":{"path":"source.sample","line_count":1}}
            transcript=run_mcp_session([sys.executable,"-B",str(PLUGIN_ROOT / "mcp_server.py")],
                                       cwd=PLUGIN_ROOT,env=environment,calls=calls)
            for name,result in transcript.results.items():
                self.assertFalse(result.is_error,name)
                self.assertEqual(payloads(result)[0]["error"]["code"],"SOURCE_HASH_MISMATCH")
            transcript=run_mcp_session([sys.executable,"-B",str(PLUGIN_ROOT / "mcp_server.py")],
                                       cwd=PLUGIN_ROOT,env=environment,
                                       calls={"read_source_evidence":{"path":path,"line_count":1}})
            self.assertEqual(payloads(transcript.results["read_source_evidence"])[0]["error"]["code"],
                             "SOURCE_HASH_MISMATCH")

    def session(self, vault, calls):
        try:
            import mcp  # noqa: F401
        except ImportError:
            self.skipTest("MCP runtime dependency is unavailable")
        declaration = json.loads((PLUGIN_ROOT / "mcp.json").read_text(encoding="utf-8"))
        server = declaration["mcpServers"]["tradingbot_knowledge"]
        environment = os.environ.copy()
        environment.pop("TRADINGBOT_ENGINE_ROOT", None)
        environment["TRADINGBOT_KNOWLEDGE_VAULT"] = str(vault)
        environment["TRADINGBOT_PLUGIN_PYTHON"] = sys.executable
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryDirectory() as temporary:
            environment["TRADINGBOT_PLUGIN_CONFIG"] = str(Path(temporary) / "absent-config.json")
            transcript = run_mcp_session([server["command"], *server["args"]],
                                         cwd=PLUGIN_ROOT, env=environment, calls=calls)
            self.assertEqual(list(Path(temporary).iterdir()), [], "Launcher wrote a user configuration")
        self.assertTrue(transcript.initialized)
        self.assertEqual(set(transcript.listed_tools), TOOLS)
        return transcript

    def test_all_eight_tools_use_local_evidence_and_explicit_empty_data_errors(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        source_id = next(key for key, row in sorted(entities.items())
                         if row["type"] == "source" and row.get("source_path")
                         and (roots.vault / row["source_path"]).stat().st_size)
        registry = json.loads((roots.vault / "06_SOURCE/References/registry.json").read_text(encoding="utf-8-sig"))
        reference = registry["references"][0]
        calls = {
            "search_knowledge": {"query": "algorithm.order.b", "limit": 25},
            "get_knowledge": {"entity_id": "algorithm.orderaudit"},
            "trace_relations": {"entity_id": "algorithm.orderaudit"},
            "get_dataset": {"entity_id": "data.missing-dataset"},
            "get_raw_window": {"entity_id": "data.missing-window", "include_rows": True},
            "read_source_evidence": {"path": source_id, "start_line": 1, "line_count": 1},
            "read_algorithm_reference_evidence": {"reference_id": reference["id"],
                                                  "start_line": 1, "line_count": 1},
            "verify_vault": {"mode": "full-data"},
        }
        before = snapshot_files([roots.vault])
        transcript = self.session(roots.vault, calls)
        decoded = {}
        for name, result in transcript.results.items():
            self.assertFalse(result.is_error, name)
            decoded[name] = payloads(result)
            self.assertTrue(decoded[name], name)
        search_rows = [row for item in decoded["search_knowledge"]
                       for row in (item if isinstance(item, list) else [item])]
        self.assertIn("algorithm.order.b", [row["id"] for row in search_rows])
        audit = decoded["get_knowledge"][0]
        self.assertEqual(audit["id"], "algorithm.orderaudit")
        self.assertEqual(audit["status"], "active")
        self.assertIsNone(audit["warning"])
        self.assertTrue(decoded["trace_relations"][0]["outgoing"])
        for name in ("get_dataset", "get_raw_window"):
            self.assertEqual(decoded[name][0]["ok"], False, name)
            self.assertEqual(decoded[name][0]["error"]["code"], "ENTITY_NOT_FOUND", name)
        source = decoded["read_source_evidence"][0]
        self.assertEqual(source["path"], entities[source_id]["source_path"])
        self.assertEqual(source["sha256"], hashlib.sha256((roots.vault / source["path"]).read_bytes()).hexdigest())
        evidence = decoded["read_algorithm_reference_evidence"][0]
        self.assertEqual(evidence["sha256"], reference["sha256"])
        self.assertEqual(evidence["source_location"], "vault_local")
        self.assertEqual(evidence["external_verification"], "optional_not_configured")
        verified = decoded["verify_vault"][0]
        self.assertTrue(verified["ok"], verified["errors"])
        self.assertEqual(verified["data_status"], "EMPTY_BY_DESIGN")
        self.assertEqual(verified["registered_datasets"], 0)
        self.assertEqual(verified["registered_windows"], 0)
        assert_unchanged(before, snapshot_files([roots.vault]))

    def test_invalid_public_requests_remain_structured_through_stdio(self):
        roots = require_real_roots(self)
        transcript = self.session(roots.vault, {
            "search_knowledge": {"query": ""},
            "read_source_evidence": {"path": "06_SOURCE/Code/../outside.py"},
            "verify_vault": {"mode": "unsupported"},
        })
        expected = {"search_knowledge": "INVALID_REQUEST",
                    "read_source_evidence": "PATH_OUTSIDE_ALLOWED_ROOT",
                    "verify_vault": "INVALID_REQUEST"}
        for name, result in transcript.results.items():
            self.assertFalse(result.is_error, name)
            response = payloads(result)[0]
            self.assertFalse(response["ok"], name)
            self.assertEqual(response["error"]["code"], expected[name])
