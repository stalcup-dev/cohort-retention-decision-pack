from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str]) -> None:
    print(f"RUN {label}: {' '.join(command)}")
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"FAILED {label} (exit={result.returncode})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full decision-pack flow in one command.")
    parser.add_argument(
        "--input",
        required=True,
        help="Raw input path, e.g. data_raw/OnlineRetailII.xlsx",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path
    if not input_path.exists():
        raise SystemExit(f"Missing input file: {input_path}")

    started_at = datetime.now(timezone.utc)
    print(f"zero_to_decision=start input={input_path}")

    run_step(
        "pipeline",
        [sys.executable, "scripts/run_pipeline.py", "--input", str(input_path)],
    )
    run_step("smoke", [sys.executable, "scripts/smoke_pipeline.py"])
    run_step("final_pack", [sys.executable, "scripts/build_final_pack.py"])

    ended_at = datetime.now(timezone.utc)
    minutes = (ended_at - started_at).total_seconds() / 60.0
    print(f"zero_to_decision=PASS elapsed_minutes={minutes:.2f}")
    print("artifact_story_pdf=exports/cohort_retention_story.pdf")
    print("artifact_story_html=exports/cohort_retention_story.html")
    print("artifact_memo=docs/DECISION_MEMO_1PAGE.md")
    print("artifact_final_pack=exports/final_decision_pack_v1")


if __name__ == "__main__":
    main()
