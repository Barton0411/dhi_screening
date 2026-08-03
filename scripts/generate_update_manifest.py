#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = (
    "https://genetic-improve.oss-cn-beijing.aliyuncs.com/tools/dhi-screening"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_download(path: Path, version: str, base_url: str) -> dict:
    return {
        "download_url": (
            f"{base_url.rstrip('/')}/releases/v{version}/{quote(path.name)}"
        ),
        "sha256": file_sha256(path),
        "size": path.stat().st_size,
    }


def generate_manifest(
    windows_installer: Path,
    macos_installer: Path,
    base_url: str = DEFAULT_BASE_URL,
    published_at: str | None = None,
) -> dict:
    version = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    notes = json.loads(
        (PROJECT_ROOT / "release_notes.json").read_text(encoding="utf-8")
    )
    expected = {
        windows_installer: f"DHI-Screening-v{version}-Windows-Setup.exe",
        macos_installer: f"DHI-Screening-v{version}-macOS.dmg",
    }
    for path, expected_name in expected.items():
        if not path.is_file() or path.name != expected_name:
            raise ValueError(f"安装包文件名与 VERSION 不一致: {path.name}")
    return {
        "schema_version": 1,
        "version": version,
        "published_at": published_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "force_update": notes.get("force_update") is True,
        "downloads": {
            "windows": build_download(windows_installer, version, base_url),
            "macos": build_download(macos_installer, version, base_url),
        },
        "changes": [str(item).strip() for item in notes.get("changes", [])],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", required=True, type=Path)
    parser.add_argument("--macos", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    manifest = generate_manifest(args.windows, args.macos, args.base_url)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "version.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    checksum_lines = []
    for path in (args.windows, args.macos):
        checksum_lines.append(f"{file_sha256(path)}  {path.name}")
    (args.output_dir / "SHA256SUMS.txt").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    notes = [f"# DHI筛查助手 v{manifest['version']}", "", "## 更新内容", ""]
    notes.extend(f"- {item}" for item in manifest["changes"])
    (args.output_dir / "RELEASE_NOTES.md").write_text(
        "\n".join(notes) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
