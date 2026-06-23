# -*- coding: utf-8 -*-
"""Phase 353: first-run branded runtime identity contract.

PyQt-free contract for splash, login and activation surfaces.  Phase 352
introduced the token layer; this module describes the runtime screen structure
that should consume those tokens.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

FIRST_RUN_PHASE = 353


@dataclass(frozen=True)
class FirstRunSurfaceSpec:
    key: str
    object_names: Sequence[str]
    token_keys: Sequence[str]
    description: str


FIRST_RUN_SURFACES: Sequence[FirstRunSurfaceSpec] = (
    FirstRunSurfaceSpec(
        "splash",
        ("startupCard", "firstRunBrandPanel", "firstRunProgressTrack", "firstRunStageChip"),
        ("first_run_panel_bg", "first_run_panel_text", "splash_progress_bg", "splash_progress_chunk"),
        "Startup splash with logo, progress, stage chips and calm branded gradient.",
    ),
    FirstRunSurfaceSpec(
        "login",
        ("loginCard", "firstRunBrandPanel", "firstRunFormPanel", "firstRunPrimary"),
        ("first_run_panel_bg", "first_run_form_bg", "first_run_chip_bg", "first_run_card_border"),
        "Split login surface: brand side panel plus focused credentials form.",
    ),
    FirstRunSurfaceSpec(
        "activation",
        ("activationCard", "firstRunBrandPanel", "activationDevicePanel", "licenseStatusBadge"),
        ("activation_card_bg", "activation_device_bg", "license_status_bg", "first_run_card_border"),
        "License activation surface with product identity, status and device context.",
    ),
)

REQUIRED_FIRST_RUN_TOKEN_KEYS: Sequence[str] = tuple(
    sorted({token for surface in FIRST_RUN_SURFACES for token in surface.token_keys})
)

REQUIRED_FIRST_RUN_OBJECT_NAMES: Sequence[str] = tuple(
    sorted({obj for surface in FIRST_RUN_SURFACES for obj in surface.object_names})
)


def validate_first_run_tokens(tokens: Mapping[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for key in REQUIRED_FIRST_RUN_TOKEN_KEYS:
        if not str(tokens.get(key, "")).strip():
            issues.setdefault("missing_tokens", []).append(key)
    return issues


def first_run_identity_matrix(tokens: Mapping[str, str] | None = None) -> List[Dict[str, object]]:
    token_map = tokens or {}
    rows: List[Dict[str, object]] = []
    for surface in FIRST_RUN_SURFACES:
        missing = [key for key in surface.token_keys if token_map and key not in token_map]
        rows.append({
            "key": surface.key,
            "description": surface.description,
            "object_count": len(surface.object_names),
            "token_count": len(surface.token_keys),
            "present": not missing,
            "missing": ",".join(missing),
        })
    return rows


__all__ = [
    "FIRST_RUN_PHASE",
    "FirstRunSurfaceSpec",
    "FIRST_RUN_SURFACES",
    "REQUIRED_FIRST_RUN_TOKEN_KEYS",
    "REQUIRED_FIRST_RUN_OBJECT_NAMES",
    "validate_first_run_tokens",
    "first_run_identity_matrix",
]
