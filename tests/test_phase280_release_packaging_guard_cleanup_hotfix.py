# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_template_loader_no_legacy_nested_fstring_no_data_hazard() -> None:
    source = (ROOT / "alrajhi_client" / "printing" / "_template_loader.py").read_text(encoding="utf-8")
    assert '_fallback_text("no_data")}</td>' not in source
    assert 'no_data_text = html.escape(_fallback_text("no_data"))' in source


def test_release_packaging_guard_cleans_generated_cache_artifacts() -> None:
    cache = ROOT / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "phase280_guard_test.pyc").write_bytes(b"cache")
    result = run_tool("tools/release_packaging_guard.py")
    assert result.returncode == 0, result.stdout
    assert "Release packaging guard passed." in result.stdout
    assert not cache.exists()


def test_release_hidden_imports_guard_allows_external_dependencies() -> None:
    result = run_tool("tools/release_hidden_imports_guard.py")
    assert result.returncode == 0, result.stdout
    assert "Release hidden imports guard passed." in result.stdout


def test_windows_packaging_gate_and_release_gate_remain_clean() -> None:
    windows = run_tool("tools/windows_runtime_packaging_gate_audit.py")
    assert windows.returncode == 0, windows.stdout
    assert "issue groups: 0" in windows.stdout
    release = run_tool("tools/release_readiness_gate_audit.py")
    assert release.returncode == 0, release.stdout
    assert "issue groups: 0" in release.stdout
