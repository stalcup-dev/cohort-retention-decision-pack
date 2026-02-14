from __future__ import annotations

from pathlib import Path
import importlib.util


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "public_audit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("public_audit", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_audit_detects_forbidden_string() -> None:
    module = load_module()
    findings = module.find_forbidden_strings("Path leak C:\\Users\\test")
    assert "C:\\Users\\" in findings


def test_public_audit_reports_file_and_token() -> None:
    module = load_module()
    probe_path = REPO_ROOT / "_public_audit_probe.md"
    probe_path.write_text("token CA-999", encoding="utf-8")
    try:
        findings = module.scan_text_file(probe_path)
        assert any("forbidden string found -> CA-" in item for item in findings)
        assert any(str(probe_path) in item for item in findings)
    finally:
        if probe_path.exists():
            probe_path.unlink()


def test_public_audit_detects_internal_algorithm_token() -> None:
    module = load_module()
    probe_path = REPO_ROOT / "_public_audit_internal_probe.md"
    probe_path.write_text("debug token selection_candidates", encoding="utf-8")
    try:
        findings = module.scan_text_file(probe_path)
        assert any("forbidden string found -> selection_candidates" in item for item in findings)
    finally:
        if probe_path.exists():
            probe_path.unlink()


def test_public_audit_passes_clean_tree() -> None:
    module = load_module()
    findings = module.run_audit(REPO_ROOT)
    assert findings == []
