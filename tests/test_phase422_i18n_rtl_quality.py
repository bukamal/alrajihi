# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase422_contract_summary_ready():
    module = load_module("alrajhi_client/workspace/quality/i18n_rtl_quality_contract.py", "phase422_contract")
    summary = module.contract_summary()
    assert summary["phase"] == 422
    assert summary["supported_languages"] == ("ar", "de", "en", "fr")
    assert summary["rtl_languages"] == ("ar",)
    assert summary["critical_key_count"] >= 35
    assert summary["runtime_direction_invariant_count"] >= 5


def test_phase422_translator_directions_and_language_labels():
    from i18n import translator

    translator.load_translations()
    assert tuple(translator.SUPPORTED_LANGUAGES) == ("ar", "de", "en", "fr")
    assert translator.language_direction("ar") == "rtl"
    for lang in ("de", "en", "fr"):
        assert translator.language_direction(lang) == "ltr"
    for key in ("ui_language", "print_language", "report_language", "language_fr"):
        for lang in translator.SUPPORTED_LANGUAGES:
            translator.set_language(lang)
            value = translator.translate(key)
            assert value and value != key


def test_phase422_critical_translation_and_placeholder_audit_passes():
    from workspace.quality.i18n_rtl_quality_audit import failures, i18n_rtl_quality_rows

    rows = i18n_rtl_quality_rows(ROOT)
    assert len(rows) >= 250
    failed = failures(rows)
    assert not failed, [(row.key, row.detail) for row in failed[:20]]


def test_phase422_code_translation_usage_is_scanned_without_blocking_dynamic_keys():
    from workspace.quality.i18n_rtl_quality_audit import code_translation_key_usage, coverage_summary

    usage = code_translation_key_usage(ROOT)
    assert usage["literal_key_count"] >= 50
    assert usage["files_with_literal_keys"] >= 10
    coverage = coverage_summary(ROOT)
    assert coverage["ar_key_count"] >= 1600
    assert coverage["en_key_count"] >= 1600


def test_phase422_runtime_direction_wiring_is_present():
    from workspace.quality.i18n_rtl_quality_audit import failures, runtime_direction_rows

    rows = runtime_direction_rows(ROOT)
    failed = failures(rows)
    assert not failed, [(row.key, row.detail) for row in failed]


def test_phase422_guard_generates_matrix_and_release_gate_registered():
    result = subprocess.run([sys.executable, "tools/phase422_i18n_rtl_quality_guard.py"], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/i18n_rtl_quality_matrix.csv"
    assert matrix.exists()
    with matrix.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 260
    assert all(row["status"] == "OK" for row in rows)
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "PHASE422_I18N_RTL_QUALITY_GATE" in gate
    assert "tools/phase422_i18n_rtl_quality_guard.py" in gate
    assert "tests/test_phase422_i18n_rtl_quality.py" in gate
