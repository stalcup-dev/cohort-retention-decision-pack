from __future__ import annotations

from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public_release"

FORBIDDEN_SNIPPETS = [
    "C:\\Users\\",
    "C:/Users/",
    "private_teaching",
    "cohort_retention_teaching",
    "TEACHING_HUB",
    "TEACHING_REPORT",
    "TEACHING_ANSWER_KEY",
    "CHART_TALK_TRACKS",
]


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def contains_forbidden_snippet(path: Path) -> bool:
    if path.suffix.lower() not in {".md", ".html", ".txt", ".csv", ".json"}:
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return any(snippet in text for snippet in FORBIDDEN_SNIPPETS)


def main() -> None:
    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []

    readme_public_src = REPO_ROOT / "README_PUBLIC.md"
    if not readme_public_src.exists():
        raise SystemExit("build_public_release=FAIL (README_PUBLIC.md is required; README.md fallback disabled)")
    copy_file(readme_public_src, PUBLIC_DIR / "README_PUBLIC.md")
    copied_files.append(PUBLIC_DIR / "README_PUBLIC.md")

    required_sources = [
        (REPO_ROOT / "case_study_readme.md", PUBLIC_DIR / "case_study_readme.md"),
        (REPO_ROOT / "docs" / "DECISION_MEMO_1PAGE.md", PUBLIC_DIR / "docs" / "DECISION_MEMO_1PAGE.md"),
        (REPO_ROOT / "docs" / "HIRING_MANAGER_TLDR.md", PUBLIC_DIR / "docs" / "HIRING_MANAGER_TLDR.md"),
        (REPO_ROOT / "docs" / "SHOPIFY_ADAPTER_CONTRACT.md", PUBLIC_DIR / "docs" / "SHOPIFY_ADAPTER_CONTRACT.md"),
    ]
    for src, dst in required_sources:
        copy_file(src, dst)
        copied_files.append(dst)

    # Optional visual: include only if it does not leak machine-local paths.
    story_src = REPO_ROOT / "exports" / "cohort_retention_story.html"
    if story_src.exists():
        story_dst = PUBLIC_DIR / "exports" / "cohort_retention_story.html"
        copy_file(story_src, story_dst)
        if contains_forbidden_snippet(story_dst):
            story_dst.unlink()
        else:
            copied_files.append(story_dst)

    leaked_paths: list[Path] = []
    for path in PUBLIC_DIR.rglob("*"):
        if path.is_file() and contains_forbidden_snippet(path):
            leaked_paths.append(path)
    if leaked_paths:
        lines = "\n".join(str(path) for path in leaked_paths)
        raise SystemExit(f"build_public_release=FAIL (machine paths detected)\n{lines}")

    print(f"build_public_release=PASS (files={len(copied_files)})")


if __name__ == "__main__":
    main()
