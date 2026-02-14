from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = REPO_ROOT / "exports" / "final_decision_pack_v1"
REQUIRED_ARTIFACTS = [
    REPO_ROOT / "exports" / "cohort_retention_story.html",
    REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md",
    REPO_ROOT / "docs" / "QA_CHECKLIST.md",
    REPO_ROOT / "docs" / "DRIVER_COVERAGE_REPORT.md",
    REPO_ROOT / "docs" / "EXPERT_UPDATE.md",
    REPO_ROOT / "data_processed" / "gate_a.json",
    REPO_ROOT / "data_processed" / "scope_receipts.json",
    REPO_ROOT / "data_processed" / "chart2_net_proxy_curves.csv",
    REPO_ROOT / "data_processed" / "chart2_selection_candidates.csv",
    REPO_ROOT / "data_processed" / "confound_m2_family_all_vs_retail.csv",
]


def main() -> None:
    missing = [str(path) for path in REQUIRED_ARTIFACTS if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required artifact(s) for final pack:\n" + "\n".join(missing)
        )

    if PACK_ROOT.exists():
        shutil.rmtree(PACK_ROOT)
    PACK_ROOT.mkdir(parents=True, exist_ok=True)

    for src in REQUIRED_ARTIFACTS:
        rel = src.relative_to(REPO_ROOT)
        dst = PACK_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    print(f"build_final_pack=PASS (path={PACK_ROOT}, files={len(REQUIRED_ARTIFACTS)})")


if __name__ == "__main__":
    main()

