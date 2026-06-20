# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from workspace.documents.document_contract import DocumentDescriptor, descriptor_for


@dataclass(frozen=True)
class PartyShellDescriptor:
    party_type: str
    descriptor: DocumentDescriptor
    api_resource: str
    workspace_route: str
    list_route: str
    supports_statement: bool = True
    supports_invoices: bool = True
    supports_vouchers: bool = True


PARTY_SHELLS: dict[str, PartyShellDescriptor] = {
    'customer': PartyShellDescriptor(
        party_type='customer',
        descriptor=descriptor_for('customer'),
        api_resource='/api/customers',
        workspace_route="open_party_document('customer')",
        list_route='customers',
    ),
    'supplier': PartyShellDescriptor(
        party_type='supplier',
        descriptor=descriptor_for('supplier'),
        api_resource='/api/suppliers',
        workspace_route="open_party_document('supplier')",
        list_route='suppliers',
    ),
}


def party_shell_for(party_type: str) -> PartyShellDescriptor:
    return PARTY_SHELLS['supplier' if party_type == 'supplier' else 'customer']
