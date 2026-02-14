from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORTS_DIR = REPO_ROOT / "exports"
STAGE_DIR = EXPORTS_DIR / "_public_zip_stage"


def run_cmd(args: list[str]) -> None:
    result = subprocess.run(args, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing expected source path: {src}")
    shutil.copytree(src, dst)


def write_zip(zip_path: Path, stage_dir: Path) -> int:
    if zip_path.exists():
        zip_path.unlink()

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(path for path in stage_dir.rglob("*") if path.is_file()):
            arcname = file_path.relative_to(stage_dir).as_posix()
            zf.write(file_path, arcname=arcname)
            file_count += 1
    return file_count


def main() -> None:
    run_cmd([sys.executable, "scripts/build_public_release.py"])
    run_cmd([sys.executable, "scripts/public_audit.py"])

    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    copy_tree(REPO_ROOT / "public_release", STAGE_DIR / "public_release")
    copy_tree(REPO_ROOT / "public_demo", STAGE_DIR / "public_demo")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXPORTS_DIR / f"public_release_{timestamp}.zip"
    latest_zip_path = EXPORTS_DIR / "public_release_latest.zip"
    archived_count = write_zip(zip_path, STAGE_DIR)
    write_zip(latest_zip_path, STAGE_DIR)

    shutil.rmtree(STAGE_DIR)
    print(
        f"build_public_zip=PASS (path={zip_path}, latest={latest_zip_path}, files={archived_count})"
    )


if __name__ == "__main__":
    main()
