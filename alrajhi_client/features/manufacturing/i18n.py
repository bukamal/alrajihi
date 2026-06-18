# -*- coding: utf-8 -*-
from __future__ import annotations

from i18n.translator import translate


def tr(key: str, **kwargs) -> str:
    return translate(key, **kwargs)
