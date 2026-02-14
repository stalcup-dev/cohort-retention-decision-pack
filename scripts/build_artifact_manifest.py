from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data_processed" / "artifact_manifest.json"
DEFAULT_ARTIFACTS = [
    REPO_ROOT / "data_processed" / "chart2_net_proxy_curves.csv",
    REPO_ROOT / "data_processed" / "chart2_selection_candidates.csv",
    REPO_ROOT / "data_processed" / "scope_receipts.json",
    REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md",
    REPO_ROOT / "exports" / "cohort_retention_story.html",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    commit = proc.stdout.strip()
    return commit if commit else None


def stamp_story_html(story_path: Path, *, timestamp_utc: str, manifest_sha256: str) -> None:
    if not story_path.exists():
        raise FileNotFoundError(f"Story HTML missing for stamping: {story_path}")
    text = story_path.read_text(encoding="utf-8", errors="ignore")
    marker_prefix = "<!-- artifact_manifest_timestamp="
    lines = [line for line in text.splitlines() if not line.strip().startswith(marker_prefix)]
    marker = (
        f"<!-- artifact_manifest_timestamp={timestamp_utc} "
        f"artifact_manifest_sha256={manifest_sha256} -->"
    )
    cleaned = "\n".join(lines)
    if "</body>" in cleaned:
        cleaned = cleaned.replace("</body>", f"{marker}\n</body>", 1)
    else:
        cleaned = cleaned + "\n" + marker + "\n"
    story_path.write_text(cleaned, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build artifact manifest with hashes")
    parser.add_argument(
        "--stamp-html",
        action="store_true",
        help="Stamp story HTML with artifact manifest timestamp/hash marker.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in DEFAULT_ARTIFACTS:
        if not path.exists():
            raise FileNotFoundError(f"Missing artifact for manifest: {path}")

    timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = []
    for path in DEFAULT_ARTIFACTS:
        rows.append(
            {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "size_bytes": int(path.stat().st_size),
            }
        )

    manifest = {
        "build_timestamp_utc": timestamp_utc,
        "git_commit": git_commit(),
        "artifacts": rows,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="ascii")
    manifest_hash = sha256_file(OUT_PATH)

    if args.stamp_html:
        stamp_story_html(
            REPO_ROOT / "exports" / "cohort_retention_story.html",
            timestamp_utc=timestamp_utc,
            manifest_sha256=manifest_hash,
        )
        # Recompute hash for stamped HTML and refresh manifest consistency.
        rows = []
        for path in DEFAULT_ARTIFACTS:
            rows.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "size_bytes": int(path.stat().st_size),
                }
            )
        manifest["artifacts"] = rows
        OUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="ascii")
        manifest_hash = sha256_file(OUT_PATH)

    print(
        "artifact_manifest=PASS "
        f"(path={OUT_PATH}, artifacts={len(rows)}, build_timestamp_utc={timestamp_utc}, "
        f"manifest_sha256={manifest_hash})"
    )


if __name__ == "__main__":
    main()

