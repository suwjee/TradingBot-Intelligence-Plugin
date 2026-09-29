"""Path and metadata inputs cannot escape their declared roots."""

import hashlib
from contextlib import ExitStack, contextmanager
import os
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


@contextmanager
def canary_read_boundary(canaries):
    """Fail if a public call touches a controlled file outside its root."""
    protected = {os.path.normcase(os.path.abspath(os.fspath(path))) for path in canaries}
    accesses = []
    with ExitStack() as stack:
        for name in ("stat", "open", "read_bytes", "read_text"):
            original = getattr(Path, name)

            def guarded(path, *args, _name=name, _original=original, **kwargs):
                if os.path.normcase(os.path.abspath(os.fspath(path))) in protected:
                    accesses.append(_name)
                    raise AssertionError(f"Outside canary accessed through {_name}")
                return _original(path, *args, **kwargs)

            stack.enter_context(patch.object(Path, name, guarded))
        yield accesses


class UntrustedPathTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows junction bootstrap boundary")
    def test_bootstrap_index_junction_is_rejected_before_reading_outside_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve()
            root=base / "vault"
            build_fake_vault(root,[])
            outside=base / "outside-index"
            (root / "_INDEX").rename(outside)
            link=root / "_INDEX"
            created=subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                                   capture_output=True, text=True)
            self.assertEqual(created.returncode,0,created.stderr)
            original=Path.read_text
            outside_reads=[]
            def observed(path,*args,**kwargs):
                if path.resolve().is_relative_to(outside):
                    outside_reads.append(str(path))
                return original(path,*args,**kwargs)
            try:
                with patch.object(Path,"read_text",observed):
                    with self.assertRaisesRegex(RuntimeError,"PATH_OUTSIDE_ALLOWED_ROOT"):
                        with plugin_reader(root):
                            pass
                self.assertEqual(outside_reads,[],"Bootstrap must not read JSON through an outside junction")
            finally:
                link.rmdir()

    def test_public_routes_reject_escape_before_outside_canary_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, engine = base / "vault", base / "engine"
            canaries = [base / "outside.py", base / "outside.json", base / "outside.md"]
            for canary in canaries:
                canary.write_text("controlled outside content\n", encoding="utf-8")
            source_path = "06_SOURCE/Code/../../../outside.py"
            raw_path = "08_DATA/Raw/../../../outside.json"
            reference_path = "engine/algorithms/../../../outside.md"
            entities = [
                EntitySpec("source.escape", "06_SOURCE/escape.md", "source", "active",
                           "canonical", "Source escape", "Synthetic source.",
                           {"source_path": source_path}),
                EntitySpec("data.escape", "08_DATA/escape.md", "data", "active",
                           "canonical", "Dataset escape", "Synthetic data.",
                           {"data_kind": "dataset", "raw_path": raw_path}),
                EntitySpec("data.window.escape", "08_DATA/window-escape.md", "data", "active",
                           "canonical", "Window escape", "Synthetic data.",
                           {"data_kind": "window", "raw_path": raw_path,
                            "first_epoch": 1, "last_epoch": 2}),
            ]
            reference = {"id": "reference.escape", "repository_relative_path": reference_path,
                         "local_path": "06_SOURCE/Code/engine/algorithms/../../../../../outside.md",
                         "bytes": 1, "sha256": hashlib.sha256(b"x").hexdigest()}
            build_fake_vault(root, entities, references=[reference])
            before = snapshot_files(canaries)
            with plugin_reader(root, engine_root=engine) as reader:
                with canary_read_boundary(canaries) as accesses:
                    calls = (lambda: reader.read_evidence(source_path),
                             lambda: reader.read_evidence("source.escape"),
                             lambda: reader.get_dataset("data.escape"),
                             lambda: reader.get_window("data.window.escape", include_rows=True),
                             lambda: reader.read_algorithm_reference_evidence("reference.escape"))
                    for call in calls:
                        with self.subTest(route=call):
                            with self.assertRaises(ValueError) as raised:
                                call()
                            self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                             "PATH_OUTSIDE_ALLOWED_ROOT")
                self.assertEqual(accesses, [], "No outside canary may be stat-ed or read")
            assert_unchanged(before, snapshot_files(canaries))

    def test_source_routes_reject_traversal_and_foreign_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [])
            unsafe = ("../outside.py", "..\\outside.py", "06_SOURCE/Code/../../outside.py",
                      "06_SOURCE/Code/../outside.py", "06_SOURCE/Code/./sample.py",
                      "06_SOURCE/Code/a/../../outside.py", "06_SOURCE/Code/..\\outside.py",
                      "/foreign/source.py", "C:" + chr(92) + "foreign" + chr(92) + "source.py",
                      "C:/foreign/source.py",
                      "\\\\host\\share\\source.py", "//host/share/source.py")
            with plugin_reader(root) as reader:
                for value in unsafe:
                    with self.subTest(value=value), self.assertRaises(ValueError) as raised:
                        reader.read_evidence(value)
                    self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                     "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_malicious_dataset_raw_path_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = EntitySpec("data.bad", "08_DATA/bad.md", "data", "active", "canonical",
                             "Bad path", "Synthetic data.", {"data_kind": "dataset",
                             "raw_path": "08_DATA/Raw/../../outside.json"})
            build_fake_vault(root, [bad])
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.get_dataset("data.bad")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_malicious_window_raw_path_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = EntitySpec("data.bad.window", "08_DATA/bad-window.md", "data", "active",
                             "canonical", "Bad window", "Synthetic data.", {"data_kind": "window",
                             "raw_path": "08_DATA/Raw/..\\outside.json", "first_epoch": 1,
                             "last_epoch": 2})
            build_fake_vault(root, [bad])
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.get_window("data.bad.window", include_rows=True)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_reference_registry_rejects_unsafe_relative_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            local = "06_SOURCE/Code/engine/algorithms/Valid.md"
            content = b"valid local reference\n"
            for value in ("engine/algorithms/../outside.md", "engine/algorithms/..\\outside.md",
                          "C:/foreign.md", "//host/share/file.md"):
                with self.subTest(value=value):
                    root = base / str(len(list(base.iterdir())))
                    registry = {"id": "reference.bad", "repository_relative_path": value,
                                "local_path": local, "bytes": len(content),
                                "sha256": hashlib.sha256(content).hexdigest()}
                    build_fake_vault(root, [], references=[registry],
                                     reference_files={local: content})
                    with plugin_reader(root, engine_root=base) as reader:
                        with self.assertRaises(ValueError) as raised:
                            reader.read_algorithm_reference_evidence("reference.bad")
                        self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                         "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_symlink_source_escape_is_rejected_when_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "vault"
            build_fake_vault(root, [])
            target = base / "outside.py"
            target.write_text("outside\n", encoding="utf-8")
            link = root / "06_SOURCE/Code/escape.py"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(target)
            except OSError as exc:
                if getattr(exc, "winerror", None) in {1314, 50}:
                    self.skipTest(f"Symlink creation unavailable (WinError {exc.winerror})")
                raise
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.read_evidence("06_SOURCE/Code/escape.py")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")

    @unittest.skipUnless(os.name == "nt", "Windows junction contract")
    def test_windows_junction_escape_is_rejected_before_canary_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, outside = base / "vault", base / "outside"
            build_fake_vault(root, [])
            outside.mkdir()
            target = outside / "outside.py"
            target.write_text("controlled outside content\n", encoding="utf-8")
            link = root / "06_SOURCE/Code/escape"
            link.parent.mkdir(parents=True, exist_ok=True)
            environment = dict(os.environ, TRADINGBOT_TEST_JUNCTION=str(link),
                               TRADINGBOT_TEST_TARGET=str(outside))
            created = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                 "-Path $env:TRADINGBOT_TEST_JUNCTION -Target $env:TRADINGBOT_TEST_TARGET | Out-Null"],
                env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(created.returncode, 0, created.stderr)
            try:
                with plugin_reader(root) as reader, canary_read_boundary([target]) as accesses:
                    with self.assertRaises(ValueError) as raised:
                        reader.read_evidence("06_SOURCE/Code/escape/outside.py")
                    self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                     "PATH_OUTSIDE_ALLOWED_ROOT")
                    self.assertEqual(accesses, [])
            finally:
                # Remove only the junction entry; never recurse into its target.
                link.rmdir()
            self.assertEqual(target.read_text(encoding="utf-8"), "controlled outside content\n")
