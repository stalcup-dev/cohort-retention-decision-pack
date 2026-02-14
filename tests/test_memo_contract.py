from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MEMO_PATH = REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md"


def test_memo_contains_targets_success_criteria_and_guardrails() -> None:
    text = MEMO_PATH.read_text(encoding="utf-8")

    for family in ["Seasonal", "Home_Fragrance", "Bags"]:
        assert family in text, f"Missing target family in memo: {family}"

    assert (
        "Success criteria" in text or "Decision thresholds" in text
    ), "Memo missing Success criteria/Decision thresholds section"
    assert "Guardrails" in text, "Memo missing Guardrails line/section"
    assert "North Star Metric" in text, "Memo missing North Star Metric section"
    assert "Single High-Leverage Insight" in text, "Memo missing insight section"
    assert "Tradeoffs" in text, "Memo missing Tradeoffs section"
    assert "What we'd do next (2 weeks)" in text, "Memo missing 2-week plan section"
