"""Bootstrap script for TidyForge development environment.

Usage:
    python infra/scripts/bootstrap.py

Checks prerequisites and runs initial setup.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def check(label: str, ok: bool, fix: str = "") -> bool:
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok and fix:
        print(f"         Fix: {fix}")
    return ok


def main() -> None:
    print("TidyForge Bootstrap")
    print("=" * 40)
    repo_root = Path(__file__).resolve().parent.parent.parent

    all_ok = True

    # Python version
    major, minor = sys.version_info[:2]
    all_ok &= check(
        f"Python {major}.{minor} (need >= 3.11)",
        (major, minor) >= (3, 11),
        "Install Python 3.11+ from python.org",
    )

    # uv
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        uv_ok = result.returncode == 0
        uv_ver = result.stdout.strip() if uv_ok else "not found"
    except FileNotFoundError:
        uv_ok = False
        uv_ver = "not found"

    all_ok &= check(
        f"uv ({uv_ver})",
        uv_ok,
        "Install uv: pip install uv  (or see https://docs.astral.sh/uv/)",
    )

    # pyproject.toml exists
    all_ok &= check(
        "pyproject.toml exists",
        (repo_root / "pyproject.toml").exists(),
    )

    if not all_ok:
        print("\nSome checks failed. Fix the issues above and re-run.")
        sys.exit(1)

    print("\nAll checks passed. Running uv sync...")
    subprocess.run(["uv", "sync"], cwd=repo_root, check=True)

    print("\nRunning tests...")
    subprocess.run(["uv", "run", "pytest", "--tb=short", "-q"], cwd=repo_root)

    print("\nBootstrap complete!")


if __name__ == "__main__":
    main()
