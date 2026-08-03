import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_update_manifest.py"
SPEC = importlib.util.spec_from_file_location("manifest_generator", SCRIPT_PATH)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class ReleaseManifestTests(unittest.TestCase):
    def test_generates_both_platform_downloads(self):
        version = (Path(__file__).resolve().parents[1] / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            windows = temp_path / f"DHI-Screening-v{version}-Windows-Setup.exe"
            macos = temp_path / f"DHI-Screening-v{version}-macOS.dmg"
            windows.write_bytes(b"synthetic windows installer")
            macos.write_bytes(b"synthetic macos installer")

            manifest = GENERATOR.generate_manifest(
                windows, macos, published_at="2026-08-03T00:00:00+00:00"
            )

        self.assertEqual(manifest["version"], version)
        self.assertEqual(set(manifest["downloads"]), {"windows", "macos"})
        self.assertEqual(len(manifest["downloads"]["windows"]["sha256"]), 64)
        self.assertEqual(len(manifest["downloads"]["macos"]["sha256"]), 64)
        json.dumps(manifest, ensure_ascii=False)

    def test_rejects_noncanonical_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            windows = temp_path / "wrong.exe"
            macos = temp_path / "wrong.dmg"
            windows.write_bytes(b"x")
            macos.write_bytes(b"y")
            with self.assertRaises(ValueError):
                GENERATOR.generate_manifest(windows, macos)
