# -*- coding: utf-8 -*-
"""Phase410 Basit release-candidate freeze contract.

This import-safe contract freezes the Phase401-409 Basit-inspired visual stack
behind a release-candidate manifest.  It does not change runtime behaviour; it
binds the accepted UI/printing surfaces to the project release gates so the
next ZIP can be treated as a stable RC baseline.
"""
from __future__ import annotations

BASIT_RELEASE_CANDIDATE_CONTRACT = {
    "phase": 410,
    "name": "basit_release_candidate_freeze",
    "release_candidate": "RC1",
    "purpose": "Freeze the accepted Basit-inspired visual system as a release-candidate baseline.",
    "depends_on": (
        "BASIT_FINAL_ACCEPTANCE_CONTRACT",
        "release_readiness_gate",
        "windows_runtime_packaging_gate",
        "release_packaging_guard",
        "release_hidden_imports_guard",
    ),
    "locked_phase_range": (401, 409),
    "required_outputs": (
        "tools/audit_outputs/basit_final_acceptance_matrix.csv",
        "tools/audit_outputs/basit_final_acceptance_report.md",
        "tools/audit_outputs/basit_release_candidate_matrix.csv",
        "tools/audit_outputs/basit_release_candidate_manifest.md",
        "tools/audit_outputs/basit_release_candidate_manifest.json",
    ),
    "freeze_rule": (
        "A release candidate is valid only when the Basit final acceptance audit, "
        "release readiness gate, packaging guard and hidden-import guard are present "
        "and the Phase401-409 visual stack remains fully registered."
    ),
}


def locked_phase_range() -> tuple[int, int]:
    return tuple(BASIT_RELEASE_CANDIDATE_CONTRACT["locked_phase_range"])
