# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TabKind(str, Enum):
    SINGLETON = "singleton"
    DOCUMENT = "document"
    TRANSIENT = "transient"


@dataclass(frozen=True)
class TabState:
    tab_id: str
    title: str
    kind: TabKind = TabKind.SINGLETON
    icon_name: str = "fa5s.folder-open"
    dirty: bool = False
