# -*- coding: utf-8 -*-
from __future__ import annotations

"""Transaction feature localization helpers.

All user-facing text inside features/transactions must go through this module
(or directly through i18n.translator.translate).  This keeps the transaction
engine aligned with the project's Arabic/German/English i18n system instead of
hardcoding labels in document tabs, grids, and print bridges.
"""

from i18n.translator import translate


def tr(key: str, **kwargs) -> str:
    return translate(key, **kwargs)


def html_bold(key: str, **kwargs) -> str:
    return f"<b>{tr(key, **kwargs)}</b>"
