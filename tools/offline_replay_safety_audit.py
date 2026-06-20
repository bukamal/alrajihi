# -*- coding: utf-8 -*-
"""Write the offline replay/idempotency safety matrix."""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.sync.offline_sync_contract import queueable_descriptors
from workspace.sync.replay_safety import (
    CONFLICT_REPLAY_STATUS_CODES,
    PERMANENT_REPLAY_STATUS_CODES,
    RETRYABLE_REPLAY_STATUS_CODES,
)


def replay_safety_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for descriptor in queueable_descriptors():
        rows.append({
            "surface_key": descriptor.surface_key,
            "api_resource": descriptor.api_resource,
            "queueable_prefixes": ",".join(descriptor.queueable_prefixes),
            "allowed_methods": ",".join(descriptor.allowed_methods),
            "conflict_policy": descriptor.conflict_policy,
            "replay_priority": descriptor.replay_priority,
            "idempotency_key_policy": descriptor.idempotency_key,
            "branch_required": descriptor.branch_required,
            "permanent_status_codes": ",".join(map(str, sorted(PERMANENT_REPLAY_STATUS_CODES))),
            "conflict_status_codes": ",".join(map(str, sorted(CONFLICT_REPLAY_STATUS_CODES))),
            "retryable_status_codes": ",".join(map(str, sorted(RETRYABLE_REPLAY_STATUS_CODES))),
        })
    return rows


def main() -> int:
    rows = replay_safety_matrix()
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "offline_replay_safety_matrix.csv"
    fieldnames = list(rows[0].keys()) if rows else ["surface_key"]
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"offline replay safety matrix: {len(rows)} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
