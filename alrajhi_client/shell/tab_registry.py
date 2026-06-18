# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional

from PyQt5.QtWidgets import QWidget

from .tab_state import TabKind


@dataclass(frozen=True)
class TabDescriptor:
    """A declarative workspace tab entry.

    Singleton tabs represent management pages such as items/reports/settings.
    Document tabs represent independently open business documents such as invoices.
    """

    tab_id: str
    title_key: str
    icon_name: str
    factory: Callable[[QWidget], QWidget]
    kind: TabKind = TabKind.SINGLETON
    allow_multiple: bool = False


class TabRegistry:
    """Small registry that decouples navigation actions from concrete widgets."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, TabDescriptor] = {}

    def register(self, descriptor: TabDescriptor) -> None:
        if not descriptor.tab_id:
            raise ValueError("tab_id is required")
        self._descriptors[descriptor.tab_id] = descriptor

    def get(self, tab_id: str) -> Optional[TabDescriptor]:
        return self._descriptors.get(tab_id)

    def ids(self) -> Iterable[str]:
        return tuple(self._descriptors.keys())

    def __contains__(self, tab_id: str) -> bool:
        return tab_id in self._descriptors
