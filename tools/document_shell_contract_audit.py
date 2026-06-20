#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project guard for the unified Document Shell contract.

This script intentionally imports only the data contract.  It does not import
PyQt widgets.  It can therefore run in CI, PyInstaller build checks, and minimal
server/client environments.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "alrajhi_client" / "workspace" / "documents" / "document_contract.py"


def _load_contract():
    spec = importlib.util.spec_from_file_location("document_shell_contract_data", CONTRACT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load document contract from {CONTRACT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_contract = _load_contract()
NETWORK_REMOTE_AVAILABLE = _contract.NETWORK_REMOTE_AVAILABLE
NETWORK_REMOTE_REQUIRED = _contract.NETWORK_REMOTE_REQUIRED
all_descriptors = _contract.all_descriptors
contract_matrix = _contract.contract_matrix
validate_all_descriptors = _contract.validate_all_descriptors


def main() -> int:
    warnings = validate_all_descriptors()
    if warnings:
        print(json.dumps(warnings, ensure_ascii=False, indent=2))
        return 1

    descriptors = all_descriptors()
    remote_docs = [
        d.document_type for d in descriptors
        if d.network_mode in {NETWORK_REMOTE_AVAILABLE, NETWORK_REMOTE_REQUIRED}
    ]
    print(f"Document Shell descriptors: {len(descriptors)}")
    print(f"Network/API-aware descriptors: {len(remote_docs)}")
    print(json.dumps(contract_matrix(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
