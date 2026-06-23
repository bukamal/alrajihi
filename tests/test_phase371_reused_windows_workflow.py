# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.workspace.quality.reused_windows_workflow_contract import (
    reused_windows_workflow_matrix,
    reused_windows_workflow_summary,
)


def test_phase371_reused_workflow_is_ready() -> None:
    summary = reused_windows_workflow_summary(Path(__file__).resolve().parents[1])
    assert summary["issues"] == 0
    assert summary["ready"] is True


def test_phase371_workflow_has_no_generic_or_portable_outputs() -> None:
    rows = reused_windows_workflow_matrix(Path(__file__).resolve().parents[1])
    forbidden_rows = [row for row in rows if row["category"] == "no_generic_or_portable_release"]
    assert forbidden_rows
    assert all(row["status"] == "pass" for row in forbidden_rows)


def test_phase371_workflow_preserves_printing_runtime_checks() -> None:
    rows = reused_windows_workflow_matrix(Path(__file__).resolve().parents[1])
    printing_rows = [row for row in rows if row["category"] == "printing_runtime_staging"]
    assert len(printing_rows) >= 8
    assert all(row["status"] == "pass" for row in printing_rows)
