#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print the Report Shell contract matrix (Phase 256)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))

from features.reports.report_shell_contract import all_report_descriptors, validate_all_report_descriptors


def main() -> int:
    warnings = validate_all_report_descriptors()
    print('Report Shell descriptors')
    print('key\ttab\ttable\tapi\tnetwork\tfilters')
    for d in all_report_descriptors():
        print(f"{d.report_key}\t{d.tab_attr}\t{d.table_attr}\t{d.api_resource}\t{d.network_mode}\t{','.join(d.filters)}")
    if warnings:
        print('WARNINGS')
        for key, items in warnings.items():
            for item in items:
                print(f'- {key}: {item}')
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
