from __future__ import annotations

from pathlib import Path
import argparse


FORBIDDEN_STRINGS = [
    "C:\\Users\\",
    "C:/Users/",
    "/Users/",
    "/home/",
    "PIP_NO_INDEX",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "index.lock",
    ".git",
    "CA-",
    "DT-",
    "Desktop\\",
    "AppData\\",
    "private_teaching",
    "cohort_retention_teaching",
    "TEACHING_HUB",
    "TEACHING_REPORT",
    "TEACHING_ANSWER_KEY",
    "CHART_TALK_TRACKS",
    "\\\\",
    "selection_candidates",
    "policy weights",
    "priority_w1",
    "priority_w2",
    "chart2_selection_candidates.csv",
]

FORBIDDEN_PUBLIC_DIRS = {"scripts", "data_raw", "data_processed", "tests"}
TEXT_EXTENSIONS = {".md", ".html", ".txt", ".csv", ".json", ".yml", ".yaml", ".py"}
REQUIRED_PUBLIC_DEMO_FILES = [
    "story_chart_1.png",
    "story_chart_2.png",
    "story_chart_3.png",
]
REQUIRED_SCREENSHOT_REFS = [
    "public_demo/story_chart_1.png",
    "public_demo/story_chart_2.png",
    "public_demo/story_chart_3.png",
]


def find_forbidden_strings(text: str) -> list[str]:
    return [token for token in FORBIDDEN_STRINGS if token in text]


def scan_text_file(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    for token in find_forbidden_strings(text):
        findings.append(f"{path}: forbidden string found -> {token}")
    return findings


def run_audit(repo_root: Path) -> list[str]:
    findings: list[str] = []

    readme_public = repo_root / "README_PUBLIC.md"
    case_study = repo_root / "case_study_readme.md"
    public_release = repo_root / "public_release"
    public_demo = repo_root / "public_demo"

    for required in [readme_public, case_study, public_release, public_demo]:
        if not required.exists():
            findings.append(f"missing required artifact: {required}")

    if public_demo.exists():
        for file_name in REQUIRED_PUBLIC_DEMO_FILES:
            expected = public_demo / file_name
            if not expected.exists():
                findings.append(f"missing required public_demo screenshot: {expected}")

    for path in [readme_public, case_study]:
        if path.exists():
            findings.extend(scan_text_file(path))

    if readme_public.exists():
        readme_text = readme_public.read_text(encoding="utf-8", errors="ignore")
        for ref in REQUIRED_SCREENSHOT_REFS:
            if ref not in readme_text:
                findings.append(f"README_PUBLIC.md missing required screenshot reference: {ref}")
        for line in readme_text.splitlines():
            if "story_chart_" in line:
                # Enforce repo-relative screenshot refs; no absolute path forms.
                if "C:\\" in line or "C:/" in line or "/Users/" in line or "/home/" in line:
                    findings.append(f"README_PUBLIC.md screenshot reference must be repo-relative: {line.strip()}")
                if line.strip().startswith("/") or line.strip().startswith("\\"):
                    findings.append(f"README_PUBLIC.md screenshot reference must not be root-absolute: {line.strip()}")

    for folder in [public_release, public_demo]:
        if folder.exists():
            for child in folder.iterdir():
                if child.is_dir() and child.name in FORBIDDEN_PUBLIC_DIRS:
                    findings.append(f"forbidden directory in {folder.name}: {child.name}")
            for file_path in folder.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(repo_root).as_posix().lower()
                    if "teaching" in rel_path:
                        findings.append(f"{file_path}: forbidden teaching artifact in public output path")
                    findings.extend(scan_text_file(file_path))

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit public release artifacts for redaction safety.")
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    findings = run_audit(repo_root)
    if findings:
        print("public_audit=FAIL")
        for finding in findings:
            print(finding)
        raise SystemExit(1)

    print("public_audit=PASS")


if __name__ == "__main__":
    main()
