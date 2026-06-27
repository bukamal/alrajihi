# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))


def test_phase393_language_runtime_contract_passes():
    from workspace.quality.language_runtime_switch_contract import language_runtime_switch_summary

    summary = language_runtime_switch_summary(ROOT)
    assert summary["passed"] is True


def test_phase393_exception_hook_is_idempotent(monkeypatch):
    import offline_read

    calls = []

    def base_hook(exc_type, exc, tb):
        calls.append((exc_type, str(exc)))

    monkeypatch.setattr(sys, "excepthook", base_hook)
    monkeypatch.setattr(sys, "__excepthook__", base_hook)

    first = offline_read.install_offline_exception_hook()
    second = offline_read.install_offline_exception_hook()

    assert first is second
    assert getattr(sys.excepthook, "_alrajhi_offline_hook", False) is True
    sys.excepthook(RecursionError, RecursionError("boom"), None)
    assert calls == [(RecursionError, "boom")]


def test_phase393_translator_language_reload_has_no_recursion():
    from i18n import translator

    translator.load_translations()
    for lang in ("ar", "de", "en", "fr", "français", "french"):
        translator.set_language(lang)
        value = translator.translate("language_settings_saved")
        assert value and value != "language_settings_saved"
        assert translator.language_direction(translator.get_language()) in {"rtl", "ltr"}
