# -*- coding: utf-8 -*-
"""Accounting gateway factory.

Direct database and SQL access for accounting belongs behind the local gateway.
"""
from __future__ import annotations


def create_accounting_gateway():
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        # Accounting remote methods are currently exposed through the REST client
        # and consumed by the local-compatible gateway implementation where present.
        from gateways.local.accounting_gateway import LocalAccountingGateway
        return LocalAccountingGateway()

    from gateways.local.accounting_gateway import LocalAccountingGateway
    return LocalAccountingGateway()
