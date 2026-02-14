from pathlib import Path
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    git_dir = repo_root / ".git"
    probe_path = git_dir / "index.lock.probe"

    if not git_dir.exists() or not git_dir.is_dir():
        print(
            "git_lock_probe=FAIL (.git directory not found; use CI or a writable local environment for commits)"
        )
        return 2

    try:
        probe_path.write_text("probe", encoding="ascii")
        probe_path.unlink(missing_ok=True)
        print("git_lock_probe=PASS")
        return 0
    except Exception as exc:
        print(
            "git_lock_probe=FAIL "
            f"({exc}; workaround: commit via CI runner or a different local environment where .git is writable)"
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
