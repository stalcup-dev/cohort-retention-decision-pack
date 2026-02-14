from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("RUN:", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> None:
    py = sys.executable
    run([py, "scripts/build_chart_tables.py"])
    run([py, "scripts/render_memo.py"])
    run([py, "scripts/render_expert_update.py"])
    run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ".\\scripts\\export_story_html.ps1",
        ]
    )
    run([py, "scripts/verify_story_contract.py"])
    run([py, "scripts/validate_chart2_selection_artifacts.py"])
    run([py, "scripts/print_evidence_pack.py"])
    print("smoke_pipeline=PASS")


if __name__ == "__main__":
    main()

