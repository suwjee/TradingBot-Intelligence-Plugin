"""Synthetic search and relation traversal contracts."""

from concurrent.futures import ThreadPoolExecutor
import importlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def item(entity_id, title, body="Synthetic text", *, status="active", authority="canonical", type="concept"):
    return EntitySpec(entity_id, f"01_CONCEPT/{title}.md", type, status, authority, title, body)


class SearchRelationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        build_fake_vault(self.root, [
            item("concept.alpha", "Alpha", "Persian کندل and shared term"),
            item("concept.beta", "Beta", "shared term"),
            item("concept.gamma", "Gamma", "shared term"),
            item("concept.hidden", "Hidden", "shared term", status="pending", authority="non-canonical"),
            item("data.utf8", "یادداشت", "محتوای فارسی کندل and shared term", type="data"),
        ], relations=[
            {"from": "concept.alpha", "type": "depends_on", "to": "concept.beta"},
            {"from": "concept.beta", "type": "supports", "to": "concept.gamma"},
            {"from": "concept.gamma", "type": "relates_to", "to": "concept.alpha"},
            {"from": "concept.alpha", "type": "affects", "to": "concept.hidden"},
        ])

    def test_exact_partial_id_and_persian_content_search(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(reader.search("Alpha")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("Alph")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("concept.beta")[0]["id"], "concept.beta")
            self.assertEqual({row["id"] for row in reader.search("کندل")},
                             {"concept.alpha", "data.utf8"})
            self.assertEqual(reader.search("یادداشت")[0]["file"], "01_CONCEPT/یادداشت.md")

    def test_multiple_matches_filters_and_explicit_diagnostic_inclusion(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(len(reader.search("shared")), 4)
            self.assertEqual([r["id"] for r in reader.search("shared", entity_type="data")], ["data.utf8"])
            self.assertEqual([r["id"] for r in reader.search("shared", entity_type="concept")],
                             ["concept.alpha", "concept.beta", "concept.gamma"])
            self.assertEqual([r["id"] for r in reader.search("shared", authority="non-canonical")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", status="pending")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", include_pending=True, status="pending")],
                             ["concept.hidden"])
            self.assertEqual([r["id"] for r in reader.search("shared", include_noncanonical=True,
                                                             authority="non-canonical")], ["concept.hidden"])

    def test_empty_no_result_pagination_and_tie_order(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError):
                reader.search(" ")
            self.assertEqual(reader.search("absentvalue"), [])
            pages = [reader.search("shared", limit=1, offset=n) for n in range(4)]
            self.assertEqual([page[0]["id"] for page in pages],
                             ["concept.alpha", "concept.beta", "concept.gamma", "data.utf8"])
            self.assertTrue(pages[0][0]["truncated"])
            self.assertEqual(pages[0][0]["next_offset"], 1)
            self.assertEqual(pages[3][0]["next_offset"], None)
            self.assertEqual(reader.search("shared", offset=99), [])

    def test_direction_depth_cycle_and_deterministic_traversal(self):
        with plugin_reader(self.root) as reader:
            outgoing = reader.relations("concept.alpha", direction="outgoing", max_depth=1)
            self.assertEqual([r["entity_id"] for r in outgoing["traversal"]], ["concept.beta"])
            incoming = reader.relations("concept.alpha", direction="incoming", max_depth=1)
            self.assertEqual([r["entity_id"] for r in incoming["traversal"]], ["concept.gamma"])
            both = reader.relations("concept.alpha", direction="both", max_depth=2)
            self.assertEqual([r["entity_id"] for r in both["traversal"]],
                             ["concept.beta", "concept.gamma"])
            deep = reader.relations("concept.alpha", direction="outgoing", max_depth=5)
            self.assertEqual([r["entity_id"] for r in deep["traversal"]],
                             ["concept.beta", "concept.gamma"])
            self.assertEqual(deep, reader.relations("concept.alpha", direction="outgoing", max_depth=5))

    def test_missing_target_quarantine_and_max_depth(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError) as caught:
                reader.relations("concept.missing")
            self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "ENTITY_NOT_FOUND")
            self.assertNotIn("concept.hidden", [e["to"] for e in reader.relations("concept.alpha")["outgoing"]])
            self.assertIn("concept.hidden", [e["to"] for e in reader.relations(
                "concept.alpha", include_quarantined=True)["outgoing"]])
            for depth in (0, 6):
                with self.assertRaises(ValueError):
                    reader.relations("concept.alpha", max_depth=depth)

    def test_independent_concurrent_reads_are_isolated_and_repeatable(self):
        with plugin_reader(self.root) as reader:
            api = importlib.import_module("mcp_server")
            def call(index):
                if index % 3 == 2:
                    return api.trace_relations("concept.alpha", direction="outgoing", max_depth=3)
                if index % 3 == 1:
                    return api.get_knowledge("concept.alpha")
                return api.search_knowledge("shared", limit=2)

            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(call, range(21)))
            for kind in range(3):
                self.assertTrue(all(result == results[kind] for result in results[kind::3]))
            results[0][0]["id"] = "mutated"
            self.assertEqual(results[3][0]["id"], "concept.alpha")
            results[1]["id"] = "mutated"
            self.assertEqual(results[4]["id"], "concept.alpha")


if __name__ == "__main__":
    unittest.main()
