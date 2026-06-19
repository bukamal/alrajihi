# -*- coding: utf-8 -*-
"""Runtime-safe access to printing templates.

PyInstaller can expose ``alrajhi_client/printing`` as a top-level ``printing``
package because the release build passes ``--paths alrajhi_client``.  Some
Windows builds have therefore loaded ``printing.__init__`` but missed the
``printing.print_templates`` submodule inside the PYZ archive.  This helper keeps
startup resilient while the packaging hooks explicitly collect the real module.
"""
from __future__ import annotations

import html
import importlib
import importlib.util
import os
from functools import lru_cache
from types import ModuleType
from typing import Callable

_TEMPLATE_MODULE_NAMES = (
    ".print_templates",
    "printing.print_templates",
    "alrajhi_client.printing.print_templates",
)


def _load_module_from_file(path: str) -> ModuleType | None:
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("printing.print_templates", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_print_templates() -> ModuleType | None:
    """Return the real print_templates module when available.

    The normal relative import is preferred.  Absolute package names and a file
    based fallback cover frozen one-dir layouts where templates are present as
    data next to this package but not registered in the PYZ import table.
    """
    package = __package__ or "printing"
    for name in _TEMPLATE_MODULE_NAMES:
        try:
            if name.startswith("."):
                return importlib.import_module(name, package=package)
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name not in {"print_templates", "printing.print_templates", "alrajhi_client.printing.print_templates"}:
                raise
        except Exception:
            continue

    here = os.path.dirname(__file__)
    for candidate in (
        os.path.join(here, "print_templates.py"),
        os.path.join(os.getcwd(), "printing", "print_templates.py"),
        os.path.join(os.getcwd(), "alrajhi_client", "printing", "print_templates.py"),
    ):
        try:
            module = _load_module_from_file(candidate)
            if module is not None:
                return module
        except Exception:
            continue
    return None


def _fallback_template(name: str) -> Callable:
    def _render(*args, **kwargs) -> str:
        title = kwargs.get("title") or name.replace("_", " ").title()
        if args:
            payload = html.escape(str(args[0]))
        else:
            payload = html.escape(str(kwargs))
        return (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>body{font-family:Arial,Tahoma,sans-serif;direction:rtl;margin:24px;}"
            "pre{white-space:pre-wrap;border:1px solid #ddd;padding:12px;}</style>"
            f"</head><body><h2>{html.escape(str(title))}</h2>"
            "<p>تم استخدام قالب طباعة احتياطي لأن قالب الطباعة الكامل غير متوفر في الحزمة.</p>"
            f"<pre>{payload}</pre></body></html>"
        )
    return _render


def require_template(name: str) -> Callable:
    module = load_print_templates()
    if module is not None and hasattr(module, name):
        template = getattr(module, name)
        if callable(template):
            return template
    return _fallback_template(name)
