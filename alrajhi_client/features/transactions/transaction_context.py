from __future__ import annotations

from dataclasses import dataclass

from .i18n import tr
from typing import Literal

DocumentType = Literal["sales_invoice", "purchase_invoice", "sales_return", "purchase_return", "restaurant_order", "pos", "draft", "quotation"]
Direction = Literal["in", "out", "neutral"]
PartyRole = Literal["customer", "supplier", "guest", "none"]
PriceMode = Literal["sale", "cost", "refund"]
StockPolicy = Literal["issue", "receive", "restore", "none"]

@dataclass(frozen=True)
class TransactionContext:
    document_type: DocumentType
    title_key: str
    direction: Direction
    party_role: PartyRole
    price_mode: PriceMode
    stock_policy: StockPolicy
    touch_mode: bool = False

    @property
    def title(self) -> str:
        return tr(self.title_key)

    @property
    def is_return(self) -> bool:
        return self.document_type in {"sales_return", "purchase_return"}

    @property
    def invoice_type(self) -> str:
        return "purchase" if self.document_type in {"purchase_invoice", "purchase_return"} else "sale"


def sales_invoice_context() -> TransactionContext:
    return TransactionContext("sales_invoice", "transaction_sales_invoice_new", "out", "customer", "sale", "issue")


def purchase_invoice_context() -> TransactionContext:
    return TransactionContext("purchase_invoice", "transaction_purchase_invoice_new", "in", "supplier", "cost", "receive")


def sales_return_context() -> TransactionContext:
    return TransactionContext("sales_return", "transaction_sales_return_new", "in", "customer", "refund", "restore")


def purchase_return_context() -> TransactionContext:
    return TransactionContext("purchase_return", "transaction_purchase_return_new", "out", "supplier", "refund", "issue")
