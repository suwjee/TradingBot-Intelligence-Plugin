"""Structured public failures and stderr-only invalid startup."""

import os
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


PLUGIN_ROOT = Path(__file__).resolve().parents[2]


class ProtocolSafetyTests(unittest.TestCase):
    def test_public_error_payload_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [EntitySpec("system.sample", "00_SYSTEM/sample.md", "system",
                                               "active", "canonical", "Sample", "Body.")])
            with plugin_reader(root) as reader:
                cases = (
                    (lambda: reader.search(""), "INVALID_REQUEST"),
                    (lambda: reader.get_entity("missing"), "ENTITY_NOT_FOUND"),
                    (lambda: reader.read_evidence("06_SOURCE/Code/missing.py"), "INVALID_REQUEST"),
                    (lambda: reader.read_algorithm_reference_evidence("missing"), "INVALID_REQUEST"),
                    (lambda: reader.get_entity("system.sample", max_bytes=1), "RESPONSE_TOO_LARGE"),
                    (lambda: reader.verify_package("other"), "INVALID_REQUEST"),
                )
                for call, expected in cases:
                    with self.subTest(expected=expected), self.assertRaises(ValueError) as raised:
                        call()
                    payload = reader.error_payload(raised.exception)
                    self.assertFalse(payload["ok"])
                    self.assertEqual(payload["error"]["code"], expected)

    def test_reference_unavailable_mismatch_and_invalid_range_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            vault, engine = base / "vault", base / "engine"
            relative = "engine/algorithms/sample.md"
            local = "06_SOURCE/Code/" + relative
            content = b"one\ntwo\n"
            reference = {"id": "reference.sample", "repository_relative_path": relative,
                         "local_path": local,
                         "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
            build_fake_vault(vault, [], references=[reference], reference_files={local: content})
            with plugin_reader(vault, engine_root=engine) as reader:
                self.assertEqual(reader.get_entity("system.authority-model")["id"],
                                 "system.authority-model")
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "REFERENCE_NOT_FOUND")
                target = engine / relative
                target.parent.mkdir(parents=True)
                target.write_bytes(b"changed\n")
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "REFERENCE_HASH_MISMATCH")
                target.write_bytes(content)
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample", 0, 1)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "INVALID_REQUEST")

    def test_invalid_vault_launcher_writes_diagnostic_only_to_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "missing-vault"
            environment = os.environ.copy()
            environment["TRADINGBOT_KNOWLEDGE_VAULT"] = str(invalid)
            environment["TRADINGBOT_PLUGIN_CONFIG"] = str(invalid / "missing-config.json")
            completed = subprocess.run([sys.executable, "-B", "mcp_server.py"],
                                       cwd=PLUGIN_ROOT, env=environment, capture_output=True,
                                       text=True, timeout=15)
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertIn("VAULT_NOT_FOUND", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
