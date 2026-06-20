# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from workspace.documents.document_contract import DocumentDescriptor, descriptor_for


@dataclass(frozen=True)
class VoucherShellDescriptor:
    descriptor: DocumentDescriptor
    api_resource: str = '/api/vouchers'
    workspace_route: str = 'open_quick_voucher'
    list_route: str = 'vouchers'
    supports_receipt: bool = True
    supports_payment: bool = True
    supports_expense: bool = True
    supports_browser_print: bool = True


VOUCHER_SHELL = VoucherShellDescriptor(descriptor=descriptor_for('voucher'))
