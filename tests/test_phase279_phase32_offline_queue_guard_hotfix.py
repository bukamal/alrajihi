from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_phase32_invoice_flow_guard_passes_after_offline_replay_contract_alignment():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "tools/phase32_invoice_flow_guard.py"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout
    assert "Phase 32 invoice/ledger guard passed." in result.stdout


def test_offline_queue_gateway_keeps_terminal_4xx_literal_for_legacy_guard():
    root = Path(__file__).resolve().parents[1]
    source = (root / "alrajhi_client/gateways/local/offline_queue_gateway.py").read_text(encoding="utf-8")
    assert "400, 401, 403, 404, 409, 422" in source
    assert "offline_queue.mark_failed" in source
    assert "offline_queue.mark_conflict" in source
