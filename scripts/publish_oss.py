#!/usr/bin/env python3
"""按版本上传双平台安装包，并最后原子式更新 latest 清单。"""

import argparse
import os
from pathlib import Path

import oss2


BUCKET_NAME = "genetic-improve"
ENDPOINT = "https://oss-cn-beijing.aliyuncs.com"
RELEASE_ROOT = "tools/dhi-screening"


def upload(bucket, local_path: Path, object_key: str, headers: dict) -> None:
    result = bucket.put_object_from_file(object_key, str(local_path), headers=headers)
    if result.status not in (200, 201):
        raise RuntimeError(f"OSS 上传失败: {object_key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", required=True, type=Path)
    args = parser.parse_args()

    access_key_id = os.environ["OSS_ACCESS_KEY_ID"]
    access_key_secret = os.environ["OSS_ACCESS_KEY_SECRET"]
    version = (Path(__file__).resolve().parents[1] / "VERSION").read_text(
        encoding="utf-8"
    ).strip()
    release_dir = args.release_dir
    files = {
        f"DHI-Screening-v{version}-Windows-Setup.exe": "application/x-msdownload",
        f"DHI-Screening-v{version}-macOS.dmg": "application/x-apple-diskimage",
        "version.json": "application/json; charset=utf-8",
        "SHA256SUMS.txt": "text/plain; charset=utf-8",
        "RELEASE_NOTES.md": "text/markdown; charset=utf-8",
    }
    for name in files:
        if not (release_dir / name).is_file():
            raise FileNotFoundError(name)

    bucket = oss2.Bucket(
        oss2.Auth(access_key_id, access_key_secret), ENDPOINT, BUCKET_NAME
    )
    release_prefix = f"{RELEASE_ROOT}/releases/v{version}"
    for name, content_type in files.items():
        upload(
            bucket,
            release_dir / name,
            f"{release_prefix}/{name}",
            {
                "Content-Type": content_type,
                "Cache-Control": "public,max-age=31536000,immutable",
            },
        )

    # 安装包和不可变清单全部成功后，最后更新 latest 指针。
    upload(
        bucket,
        release_dir / "version.json",
        f"{RELEASE_ROOT}/latest/version.json",
        {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


if __name__ == "__main__":
    main()
