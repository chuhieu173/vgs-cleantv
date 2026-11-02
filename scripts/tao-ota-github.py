#!/usr/bin/env python3
"""
Chuẩn bị thư mục dist/ và sinh file cap-nhat.json cho GitHub Releases (OTA của chuhieu173/vgs-cleantv).
Hỗ trợ cập nhật tự động:
- App chính CleanTV.apk (qua hộp thoại cập nhật OTA trong app)
- Dữ liệu ngầm (du-lieu.json, tvhome.apk, mapvoice.apk) tải tự động vào filesDir/ota/
- Kèm SonyKeepAlive.apk trong mỗi bản phát hành
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KHO = os.environ.get("GITHUB_REPOSITORY", "chuhieu173/vgs-cleantv")


def sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main():
    gradle_text = (ROOT / "app/build.gradle.kts").read_text(encoding="utf-8")
    code = int(re.search(r"versionCode\s*=\s*(\d+)", gradle_text).group(1))
    name = re.search(r'versionName\s*=\s*"([^"]+)"', gradle_text).group(1)

    apk_src = ROOT / "app/build/outputs/apk/release/app-release.apk"
    if not apk_src.is_file():
        sys.exit(f"Thiếu file APK: {apk_src}")

    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    apk_name = f"CleanTV-{name}.apk"
    shutil.copy2(apk_src, dist / apk_name)
    shutil.copy2(apk_src, dist / "CleanTV.apk")

    keepalive_src = ROOT / "keepalive/build/outputs/apk/release/keepalive-release.apk"
    if not keepalive_src.is_file():
        keepalive_src = ROOT / "SonyKeepAlive.apk"
    if keepalive_src.is_file():
        shutil.copy2(keepalive_src, dist / "SonyKeepAlive.apk")

    assets = ROOT / "app/src/main/assets"
    du_lieu_obj = {}
    for fname in ["du-lieu.json", "tvhome.apk", "mapvoice.apk"]:
        f = assets / fname
        if f.is_file():
            shutil.copy2(f, dist / fname)
            du_lieu_obj[fname] = {
                "phienBan": sha16(f),
                "url": f"https://github.com/{KHO}/releases/latest/download/{fname}",
                "co": f.stat().st_size,
                "tuBan": code,
            }

    tz_vn = datetime.timezone(datetime.timedelta(hours=7))
    ngay = datetime.datetime.now(tz_vn).strftime("%Y-%m-%d")
    ghi_chu = os.environ.get(
        "GHI_CHU",
        f"Bản tự động đồng bộ từ vgscity/vgs-cleantv ({name}) + Map Voice từ Circling5714/tivikit.",
    )
    ghi_chu_en = os.environ.get(
        "GHI_CHU_EN",
        f"Auto-synced from vgscity/vgs-cleantv ({name}) + Map Voice from Circling5714/tivikit.",
    )

    cap_nhat = {
        "app": {
            "versionCode": code,
            "versionName": name,
            "apk": f"https://github.com/{KHO}/releases/latest/download/{apk_name}",
            "co": apk_src.stat().st_size,
            "ghiChu": ghi_chu,
            "ghiChuEn": ghi_chu_en,
            "ngay": ngay,
        },
        "duLieu": du_lieu_obj,
    }

    (dist / "cap-nhat.json").write_text(
        json.dumps(cap_nhat, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Đã tạo gói phát hành OTA tại {dist}: CleanTV {name} (versionCode={code})")


if __name__ == "__main__":
    main()
