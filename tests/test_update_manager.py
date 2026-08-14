import hashlib
import json
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from update_manager import (
    fetch_update_manifest,
    is_newer_version,
    validate_manifest,
    verify_file_sha256,
)


def sample_manifest(version="4.02.25"):
    return {
        "schema_version": 1,
        "version": version,
        "published_at": "2026-08-03T00:00:00+00:00",
        "force_update": False,
        "downloads": {
            "windows": {
                "download_url": (
                    "https://genetic-improve.oss-cn-beijing.aliyuncs.com/"
                    f"tools/dhi-screening/releases/v{version}/"
                    f"DHI-Screening-v{version}-Windows-Setup.exe"
                ),
                "sha256": "a" * 64,
                "size": 123,
            },
            "macos": {
                "download_url": (
                    "https://genetic-improve.oss-cn-beijing.aliyuncs.com/"
                    f"tools/dhi-screening/releases/v{version}/"
                    f"DHI-Screening-v{version}-macOS.dmg"
                ),
                "sha256": "b" * 64,
                "size": 456,
            },
        },
        "changes": ["安全更新"],
    }


class UpdateManagerTests(unittest.TestCase):
    def test_version_comparison_handles_zero_padding(self):
        self.assertTrue(is_newer_version("4.02.25", "4.02.24"))
        self.assertFalse(is_newer_version("4.2.25", "4.02.25.0"))

    def test_manifest_selects_requested_platform(self):
        manifest = validate_manifest(sample_manifest(), "macos")
        self.assertEqual(manifest["platform"], "macos")
        self.assertTrue(manifest["download_url"].endswith("-macOS.dmg"))

    def test_manifest_rejects_untrusted_download_host(self):
        manifest = sample_manifest()
        manifest["downloads"]["windows"]["download_url"] = "https://example.com/a.exe"
        with self.assertRaises(ValueError):
            validate_manifest(manifest, "windows")

    def test_sha256_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "installer.bin"
            path.write_bytes(b"synthetic installer")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(verify_file_sha256(path, digest))
            self.assertFalse(verify_file_sha256(path, "0" * 64))

    @patch("update_manager.urllib_request.urlopen")
    def test_manifest_request_uses_explicit_ssl_context(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(sample_manifest()).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        fetch_update_manifest()

        self.assertIsInstance(urlopen.call_args.kwargs["context"], ssl.SSLContext)
