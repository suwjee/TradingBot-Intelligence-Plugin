"""Current public retrieval fields and portable runtime path contract."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class RetrievalContractTests(unittest.TestCase):
    def test_entity_and_search_emit_current_source_fields_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            built = build_fake_vault(root, [EntitySpec("concept.sample", "01_CONCEPT/Sample.md", "concept",
                                                       "active", "canonical", "Sample", "Synthetic word")])
            with plugin_reader(root) as reader:
                entity = reader.get_entity("concept.sample")
                expected = set(built.entities["concept.sample"]) | {"warning", "sync_review_state", "content"}
                self.assertEqual(set(entity), expected)
                for key, value in built.entities["concept.sample"].items():
                    self.assertEqual(entity[key], value)
                hit = reader.search("sample")[0]
                self.assertEqual(set(hit), (expected - {"content"}) |
                                 {"excerpt", "total_matches", "truncated", "next_offset"})
                self.assertEqual(hit["total_matches"], 1)
                self.assertFalse(hit["truncated"])
                self.assertIsNone(hit["next_offset"])
                self.assertNotIn("snippet", hit)
                self.assertNotIn("reasoning_eligibility", entity)

    def test_runtime_and_new_tests_have_no_machine_specific_paths(self):
        plugin = Path(__file__).resolve().parents[2]
        runtime = list(plugin.glob("*.py"))
        runtime.extend((plugin / "maintenance").rglob("*.py"))
        runtime.extend((plugin / "scripts").rglob("*.py"))
        tests = list((plugin / "tests").rglob("*.py"))
        # Compose all forbidden needles at runtime because this test scans itself.
        drive_suffix = ":" + chr(92)
        forbidden = tuple(letter + drive_suffix for letter in ("D", "C", "X"))
        forbidden += ("/" + "home" + "/", "/" + "Users" + "/")
        for path in sorted({*runtime, *tests}):
            with self.subTest(path=path.relative_to(plugin)):
                content = path.read_text(encoding="utf-8")
                for needle in forbidden:
                    self.assertNotIn(needle, content)


if __name__ == "__main__":
    unittest.main()
