# -*- coding: utf-8 -*-
"""Phase 422 static i18n/RTL quality audit.

The audit is intentionally free of PyQt imports.  It checks the translation
catalog, placeholder parity and the static wiring that applies direction changes
at runtime.  Real screenshots remain delegated to the Phase416 runtime harness.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import re
import sys
from typing import Iterable, Sequence

from .i18n_rtl_quality_contract import I18N_RTL_QUALITY_CONTRACT, critical_keys

ROOT = Path(__file__).resolve().parents[3]
_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True)
class I18nAuditRow:
    key: str
    category: str
    path: str
    ok: bool
    detail: str


def _read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _ensure_client_path(root: Path) -> None:
    client = str(root / "alrajhi_client")
    if client not in sys.path:
        sys.path.insert(0, client)


def _translator(root: Path):
    _ensure_client_path(root)
    from i18n import translator  # type: ignore
    translator.load_translations()
    return translator


def translation_catalog(root: Path | None = None) -> dict[str, dict[str, str]]:
    base = root or ROOT
    translator = _translator(base)
    raw = getattr(translator, "_translations", {})
    return {str(lang): dict(values) for lang, values in raw.items()}


def placeholders(text: str | None) -> frozenset[str]:
    return frozenset(_PLACEHOLDER_RE.findall(text or ""))


def _add(rows: list[I18nAuditRow], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append(I18nAuditRow(key=key, category=category, path=path, ok=bool(ok), detail=detail))


def _call_key_literals(path: Path) -> set[str]:
    """Return literal keys passed to translate()/tr().

    This is best-effort: dynamic keys are intentionally ignored and should be
    covered by surface contracts rather than guessed by static analysis.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name not in {"translate", "tr"}:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            found.add(arg.value)
    return found


def code_translation_key_usage(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    keys: set[str] = set()
    files = 0
    for path in (base / "alrajhi_client").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        found = _call_key_literals(path)
        if found:
            files += 1
            keys.update(found)
    catalog = translation_catalog(base)
    catalog_keys = set().union(*(set(values) for values in catalog.values())) if catalog else set()
    return {
        "files_with_literal_keys": files,
        "literal_key_count": len(keys),
        "missing_from_catalog": tuple(sorted(k for k in keys if k not in catalog_keys)),
    }


def critical_translation_rows(root: Path | None = None) -> list[I18nAuditRow]:
    base = root or ROOT
    translator = _translator(base)
    catalog = translation_catalog(base)
    rows: list[I18nAuditRow] = []
    languages: Sequence[str] = tuple(I18N_RTL_QUALITY_CONTRACT["supported_languages"])
    keys = critical_keys()
    for key in keys:
        ar_value = catalog.get("ar", {}).get(key)
        ar_placeholders = placeholders(ar_value)
        for lang in languages:
            value = catalog.get(lang, {}).get(key)
            _add(rows, f"critical::{key}::{lang}", "translation", "alrajhi_client/i18n/translator.py", bool(value and value != key), f"{key}/{lang} has a non-key translation")
            if value:
                _add(rows, f"placeholders::{key}::{lang}", "placeholder", "alrajhi_client/i18n/translator.py", placeholders(value) == ar_placeholders, f"{key}/{lang} placeholders match Arabic source")
        # Translate through public API as an additional fallback check.
        for lang in languages:
            translator.set_language(lang)
            translated = translator.translate(key)
            _add(rows, f"translate_api::{key}::{lang}", "api", "alrajhi_client/i18n/translator.py", bool(translated and translated != key), f"translate({key!r}) returns translated text in {lang}")
    return rows


def runtime_direction_rows(root: Path | None = None) -> list[I18nAuditRow]:
    base = root or ROOT
    translator = _translator(base)
    rows: list[I18nAuditRow] = []
    supported = tuple(I18N_RTL_QUALITY_CONTRACT["supported_languages"])
    rtl = tuple(I18N_RTL_QUALITY_CONTRACT["rtl_languages"])
    _add(rows, "supported_languages_exact", "registry", "alrajhi_client/i18n/translator.py", tuple(translator.SUPPORTED_LANGUAGES) == supported, f"supported={translator.SUPPORTED_LANGUAGES}")
    for lang in supported:
        expected = "rtl" if lang in rtl else "ltr"
        _add(rows, f"direction::{lang}", "direction", "alrajhi_client/i18n/translator.py", translator.language_direction(lang) == expected, f"{lang} direction is {expected}")
    settings = _read(base, "alrajhi_client/views/widgets/settings_widget.py")
    main = _read(base, "alrajhi_client/views/main_window.py")
    table_policy = _read(base, "alrajhi_client/ui/table_direction_policy.py")
    runtime = _read(base, "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py")
    settings_tabs = _read(base, "alrajhi_client/features/settings/settings_document_tabs.py")
    _add(rows, "settings_language_choices_cover_all_supported_languages", "settings", "alrajhi_client/features/settings/settings_document_tabs.py", settings_tabs.count("choice:ar|en|de|fr") >= 3, "UI/report/print language choices include ar/en/de/fr")
    _add(rows, "settings_applies_table_direction_tree", "runtime", "alrajhi_client/views/widgets/settings_widget.py", "apply_table_direction_tree(self, lang)" in settings and "apply_table_direction_tree(main_window, lang)" in settings, "settings language switch propagates table direction")
    _add(rows, "main_window_applies_table_direction_tree", "runtime", "alrajhi_client/views/main_window.py", "apply_table_direction_tree(self, self._current_language)" in main, "main window applies table direction after language load")
    _add(rows, "main_menu_bar_runtime_direction", "runtime", "alrajhi_client/views/main_window.py", "self.menu_bar.setLayoutDirection(qt_layout_direction(self._current_language))" in main, "top menu bar receives active language direction")
    _add(rows, "table_policy_sets_viewport_and_headers", "runtime", "alrajhi_client/ui/table_direction_policy.py", "viewport.setLayoutDirection(direction)" in table_policy and "header.setLayoutDirection(direction)" in table_policy, "table policy updates viewport and headers")
    _add(rows, "phase416_captures_ar_de_shell_snapshots", "runtime", "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py", "shell_ar_rtl_snapshot" in runtime and "shell_de_ltr_snapshot" in runtime and "for lang in (\"ar\", \"de\")" in runtime, "runtime harness captures Arabic RTL and German LTR shell snapshots")
    return rows


def coverage_summary(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    catalog = translation_catalog(base)
    ar_keys = set(catalog.get("ar", {}))
    en_keys = set(catalog.get("en", {}))
    rows: list[dict[str, object]] = []
    for lang in I18N_RTL_QUALITY_CONTRACT["supported_languages"]:
        keys = set(catalog.get(lang, {}))
        rows.append({
            "language": lang,
            "key_count": len(keys),
            "missing_from_ar": len(ar_keys - keys),
            "missing_from_en": len(en_keys - keys),
            "extra_vs_ar": len(keys - ar_keys),
        })
    return {"languages": rows, "ar_key_count": len(ar_keys), "en_key_count": len(en_keys)}


def i18n_rtl_quality_rows(root: Path | None = None) -> list[I18nAuditRow]:
    base = root or ROOT
    rows: list[I18nAuditRow] = []
    rows.extend(runtime_direction_rows(base))
    rows.extend(critical_translation_rows(base))
    usage = code_translation_key_usage(base)
    missing = tuple(usage["missing_from_catalog"])
    _add(rows, "literal_translation_key_usage_scanned", "usage", "alrajhi_client", int(usage["literal_key_count"]) >= 50, f"literal keys={usage['literal_key_count']} files={usage['files_with_literal_keys']}")
    # Dynamic/legacy keys may remain, but critical surface keys must not be missing.
    critical_missing = [key for key in critical_keys() if key in missing]
    _add(rows, "critical_literal_keys_exist_in_catalog", "usage", "alrajhi_client/i18n/translator.py", not critical_missing, f"critical missing literal keys={len(critical_missing)}")
    return rows


def failures(rows: Iterable[I18nAuditRow]) -> list[I18nAuditRow]:
    return [row for row in rows if not row.ok]


def summary(root: Path | None = None) -> dict[str, object]:
    rows = i18n_rtl_quality_rows(root)
    failed = failures(rows)
    cov = coverage_summary(root)
    return {
        "checks": len(rows),
        "failed": len(failed),
        "passed": not failed,
        "coverage": cov,
        "failed_checks": [row.key for row in failed],
    }


__all__ = [
    "I18nAuditRow",
    "code_translation_key_usage",
    "coverage_summary",
    "critical_translation_rows",
    "failures",
    "i18n_rtl_quality_rows",
    "runtime_direction_rows",
    "summary",
    "translation_catalog",
]
