"""T1/T2 真实远端端到端冒烟：对真实 GitHub Release v0.1.0 执行
查版本（应无新版，因当前版本=已发布版本）+ 真实资产下载 + SHA256 校验
+ 内置公钥验签（manifest.sig + 包.sig）。

经系统代理 127.0.0.1:1080（python 直连 api.github.com 被本机网络层拦）。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # 工程根
sys.path.insert(0, str(ROOT / "src"))

from update.channel import UpdateChannel  # noqa: E402

REPO = "Ultima-AI-Studio/Ultima-Agent"
DOWNLOAD_BASE = "https://github.com/Ultima-AI-Studio/Ultima-Agent/releases/download/v0.1.0"

PUBLIC_KEY = ROOT / "src" / "update" / "public_key.pem"

OUT_DIR = ROOT / "docs" / "reports" / "evidence" / "wo-s1-remote-update-trigger"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ch = UpdateChannel(REPO, public_key_path=PUBLIC_KEY, http_timeout=30.0)
    report: dict = {}

    # 1) RU-01 查版本：当前 0.1.0 == 已发布 v0.1.0 → 无新版（预期 None）
    info = ch.check_for_update("0.1.0")
    report["ru01_check_current_0_1_0"] = {
        "result": "no_update" if info is None else f"new={info.version}",
        "expected": "no_update (current equals latest release v0.1.0)",
    }

    # 2) RU-02 真实资产下载 + SHA256 校验（强制校验，不经版本比较）
    pkg_name = "UltimaAgent-Setup-0.1.0.exe"
    pkg_url = f"{DOWNLOAD_BASE}/{pkg_name}"
    work = OUT_DIR / "smoke"
    work.mkdir(parents=True, exist_ok=True)
    pkg_file = work / pkg_name
    if pkg_file.is_file() and pkg_file.stat().st_size > 90_000_000:
        print("using cached package", flush=True)
        pkg_data = pkg_file.read_bytes()
    else:
        pkg_data = ch._http_get(pkg_url)
        pkg_file.write_bytes(pkg_data)
    pkg_sha = hashlib.sha256(pkg_data).hexdigest()
    report["ru02_download_sha256"] = {
        "package": pkg_name,
        "size": len(pkg_data),
        "sha256": pkg_sha,
        "matches_release_digest": pkg_sha == "61d1a7df02d36a8aa68b44868f39264a434f256cc865d491c714f51424d3814b",
    }

    # 3) RU-03 真实签名资产验签（manifest.json.sig + 包.sig，内置公钥）
    manifest_data = ch._http_get(f"{DOWNLOAD_BASE}/manifest.json")
    manifest_sig = ch._http_get(f"{DOWNLOAD_BASE}/manifest.json.sig")
    pkg_sig = ch._http_get(f"{DOWNLOAD_BASE}/{pkg_name}.sig")
    (work / "manifest.json").write_bytes(manifest_data)
    (work / "manifest.json.sig").write_bytes(manifest_sig)
    (work / pkg_name).write_bytes(pkg_data)
    (work / (pkg_name + ".sig")).write_bytes(pkg_sig)

    manifest_obj = json.loads(manifest_data)
    report["ru03_manifest_fields"] = {
        "version": manifest_obj.get("version"),
        "package": manifest_obj.get("package"),
        "force_update": manifest_obj.get("force_update"),
        "release_url": manifest_obj.get("release_url"),
        "published_at": manifest_obj.get("published_at"),
    }

    try:
        ch.verify_signatures(work / "manifest.json", work / pkg_name)
        report["ru03_signature_verify"] = "PASS (manifest + package verified with client public key)"
    except Exception as exc:  # noqa: BLE001
        report["ru03_signature_verify"] = f"FAIL: {exc}"

    # 4) 篡改负向：改一个字节 → 应拒绝
    tampered = work / pkg_name
    tampered.write_bytes(b"X" + pkg_data[1:])
    try:
        ch.verify_signatures(work / "manifest.json", tampered)
        report["ru04_tamper_reject"] = "FAIL (tampered package accepted!)"
    except Exception as exc:  # noqa: BLE001
        report["ru04_tamper_reject"] = f"PASS (tampered rejected: {type(exc).__name__})"
    (work / pkg_name).write_bytes(pkg_data)  # 还原

    out_file = OUT_DIR / "smoke-t1-t2-20261028.json"
    out_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    ok = (
        report["ru01_check_current_0_1_0"]["result"] == "no_update"
        and report["ru02_download_sha256"]["matches_release_digest"]
        and report["ru03_signature_verify"].startswith("PASS")
        and report["ru04_tamper_reject"].startswith("PASS")
    )
    print(f"\nSMOKE_RESULT={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
