# -*- coding: utf-8 -*-
try:
    from .functional_close_policy import (
        FunctionalCloseTarget,
        function_close_targets,
        request_function_workspace_close,
        target_keys,
    )
except Exception:  # pragma: no cover - PyQt/runtime import fallback
    pass

