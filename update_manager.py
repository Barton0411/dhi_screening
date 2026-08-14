"""跨平台更新清单校验、下载安装包和启动安装。"""

import hashlib
import json
import os
import platform
import re
import ssl
import subprocess
import tempfile
from pathlib import Path
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import certifi

from version import get_version


UPDATE_MANIFEST_URL = (
    "https://genetic-improve.oss-cn-beijing.aliyuncs.com/"
    "tools/dhi-screening/latest/version.json"
)
ALLOWED_UPDATE_HOSTS = {"genetic-improve.oss-cn-beijing.aliyuncs.com"}
MAX_MANIFEST_BYTES = 64 * 1024
MAX_INSTALLER_BYTES = 500 * 1024 * 1024
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _create_ssl_context() -> ssl.SSLContext:
    """使用打包内置的 CA，避免 PyInstaller 环境找不到系统证书。"""
    return ssl.create_default_context(cafile=certifi.where())


def parse_version(version: str) -> tuple[int, ...]:
    normalized = str(version).strip().removeprefix("v")
    if not re.fullmatch(r"\d+(?:\.\d+){2,3}", normalized):
        raise ValueError("版本号格式无效")
    return tuple(int(part) for part in normalized.split("."))


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = list(parse_version(candidate))
    current_parts = list(parse_version(current))
    width = max(len(candidate_parts), len(current_parts))
    candidate_parts.extend([0] * (width - len(candidate_parts)))
    current_parts.extend([0] * (width - len(current_parts)))
    return candidate_parts > current_parts


def current_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    raise ValueError("当前操作系统暂不支持自动更新")


def _validate_https_url(url: str, expected_prefix: str) -> str:
    parsed = urllib_parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_UPDATE_HOSTS:
        raise ValueError("更新地址不受信任")
    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith(expected_prefix)
    ):
        raise ValueError("更新地址格式无效")
    return url


def _validate_download(download: object, version: str, target_platform: str) -> dict:
    if not isinstance(download, dict):
        raise ValueError("缺少当前平台安装包")
    expected_name = {
        "windows": f"DHI-Screening-v{version}-Windows-Setup.exe",
        "macos": f"DHI-Screening-v{version}-macOS.dmg",
    }[target_platform]
    download_url = _validate_https_url(
        str(download.get("download_url", "")).strip(),
        f"/tools/dhi-screening/releases/v{version}/",
    )
    actual_name = Path(
        urllib_parse.unquote(urllib_parse.urlparse(download_url).path)
    ).name
    if actual_name != expected_name:
        raise ValueError("安装包文件名与版本不一致")
    sha256 = str(download.get("sha256", "")).strip().lower()
    if not SHA256_PATTERN.fullmatch(sha256):
        raise ValueError("安装包校验值无效")
    size = download.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or not 0 < size <= MAX_INSTALLER_BYTES:
        raise ValueError("安装包大小无效")
    return {"download_url": download_url, "sha256": sha256, "size": size}


def validate_manifest(data: object, target_platform: str | None = None) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("版本清单格式无效")
    version = str(data.get("version", "")).strip().removeprefix("v")
    parse_version(version)
    target_platform = target_platform or current_platform()
    downloads = data.get("downloads")
    if not isinstance(downloads, dict):
        raise ValueError("安装包清单格式无效")
    selected = _validate_download(downloads.get(target_platform), version, target_platform)
    changes = data.get("changes", [])
    if not isinstance(changes, list) or len(changes) > 50:
        raise ValueError("更新说明格式无效")
    clean_changes = []
    for item in changes:
        if not isinstance(item, str) or not item.strip() or len(item) > 300:
            raise ValueError("更新说明格式无效")
        clean_changes.append(item.strip())
    return {
        "schema_version": 1,
        "version": version,
        "published_at": str(data.get("published_at", "")).strip(),
        "force_update": data.get("force_update") is True,
        "platform": target_platform,
        "changes": clean_changes,
        **selected,
    }


def fetch_update_manifest(timeout: int = 10) -> dict:
    _validate_https_url(UPDATE_MANIFEST_URL, "/tools/dhi-screening/latest/version.json")
    request = urllib_request.Request(
        UPDATE_MANIFEST_URL,
        headers={"Accept": "application/json", "User-Agent": f"dhi-screening/{get_version()}"},
    )
    with urllib_request.urlopen(
        request, timeout=timeout, context=_create_ssl_context()
    ) as response:
        raw = response.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("版本清单过大")
    return validate_manifest(json.loads(raw.decode("utf-8")))


def verify_file_sha256(path: Path, expected_sha256: str) -> bool:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_sha256.lower()


def download_installer(manifest: dict, progress_callback=None) -> Path:
    manifest = validate_manifest(
        {
            "schema_version": 1,
            "version": manifest["version"],
            "published_at": manifest.get("published_at", ""),
            "force_update": manifest.get("force_update", False),
            "changes": manifest.get("changes", []),
            "downloads": {
                manifest["platform"]: {
                    "download_url": manifest["download_url"],
                    "sha256": manifest["sha256"],
                    "size": manifest["size"],
                }
            },
        },
        manifest["platform"],
    )
    filename = Path(
        urllib_parse.unquote(urllib_parse.urlparse(manifest["download_url"]).path)
    ).name
    target_dir = Path(tempfile.gettempdir()) / "dhi-screening-updates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    partial = target.with_suffix(target.suffix + ".part")
    if target.exists() and target.stat().st_size == manifest["size"]:
        if verify_file_sha256(target, manifest["sha256"]):
            if progress_callback:
                progress_callback(100)
            return target

    request = urllib_request.Request(
        manifest["download_url"],
        headers={"User-Agent": f"dhi-screening/{get_version()}"},
    )
    downloaded = 0
    digest = hashlib.sha256()
    try:
        with urllib_request.urlopen(
            request, timeout=60, context=_create_ssl_context()
        ) as response, partial.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > manifest["size"] or downloaded > MAX_INSTALLER_BYTES:
                    raise ValueError("安装包大小与版本清单不一致")
                digest.update(chunk)
                output.write(chunk)
                if progress_callback:
                    progress_callback(min(99, int(downloaded * 100 / manifest["size"])))
        if downloaded != manifest["size"] or digest.hexdigest() != manifest["sha256"]:
            raise ValueError("安装包完整性校验失败")
        partial.replace(target)
        if progress_callback:
            progress_callback(100)
        return target
    except Exception:
        partial.unlink(missing_ok=True)
        raise


def launch_installer(path: Path) -> None:
    path = path.resolve(strict=True)
    if platform.system().lower() == "windows":
        os.startfile(str(path))
    elif platform.system().lower() == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        raise ValueError("当前操作系统暂不支持自动安装")
