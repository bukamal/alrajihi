from __future__ import annotations

from PyQt5.QtCore import QByteArray

from auth.session import UserSession
from core.services.settings_service import settings_service


class TransactionGridPreferences:
    """Per-user/per-branch/per-settings-profile layout persistence.

    Transaction screens must not instantiate QSettings directly.  The project
    already owns a settings-service/profile layer, so grid layout state is stored
    through settings_service and scoped by current user, branch, active profile,
    and document type.
    """

    def __init__(self, user_key: str | None = None):
        self.user_key = user_key or self._current_scope_key()

    def _current_scope_key(self) -> str:
        user_id = UserSession.get_current_user_id() or UserSession.get_current_username() or "anonymous"
        branch_id = UserSession.get_current_branch_id() or "global"
        try:
            profile = settings_service.get_active_profile() or {}
            profile_id = profile.get("id") or 1
        except Exception:
            profile_id = 1
        return f"users/{user_id}/branches/{branch_id}/profiles/{profile_id}"

    def key(self, document_type: str, name: str) -> str:
        return f"transactions/{self.user_key}/{document_type}/{name}"

    def _set(self, document_type: str, name: str, value) -> None:
        settings_service.set(self.key(document_type, name), value)

    def _get(self, document_type: str, name: str, default=None):
        return settings_service.get(self.key(document_type, name), default)

    def _remove(self, document_type: str, name: str) -> None:
        try:
            settings_service.set(self.key(document_type, name), "")
        except Exception:
            pass

    def save_header_state(self, grid, document_type: str) -> None:
        header = grid.horizontalHeader()
        state = header.saveState()
        try:
            encoded = bytes(state.toBase64()).decode("ascii")
        except Exception:
            encoded = ""
        self._set(document_type, "headerState", encoded)

    def restore_header_state(self, grid, document_type: str) -> None:
        encoded = self._get(document_type, "headerState", "")
        if not encoded:
            return
        try:
            state = QByteArray.fromBase64(str(encoded).encode("ascii"))
            if not state.isEmpty():
                grid.horizontalHeader().restoreState(state)
        except Exception:
            pass

    def reset_header_state(self, document_type: str) -> None:
        self._remove(document_type, "headerState")

    def save_visible_keys(self, grid, document_type: str) -> None:
        if not hasattr(grid, "visible_keys"):
            return
        self._set(document_type, "visibleKeys", ",".join(grid.visible_keys()))

    def restore_visible_keys(self, grid, document_type: str) -> bool:
        raw = self._get(document_type, "visibleKeys", "")
        if not raw:
            return False
        keys = [part.strip() for part in str(raw).split(",") if part.strip()]
        if not keys or not hasattr(grid, "apply_visible_keys"):
            return False
        grid.apply_visible_keys(keys)
        return True

    def save_active_preset(self, document_type: str, preset_name: str) -> None:
        self._set(document_type, "activePreset", str(preset_name or ""))

    def active_preset(self, document_type: str, default: str = "manager") -> str:
        return str(self._get(document_type, "activePreset", default) or default)

    def save_auto_responsive(self, document_type: str, enabled: bool) -> None:
        self._set(document_type, "autoResponsive", "true" if enabled else "false")

    def auto_responsive(self, document_type: str, default: bool = True) -> bool:
        value = self._get(document_type, "autoResponsive", "true" if default else "false")
        return str(value).lower() in ("1", "true", "yes", "on")

    def reset_document_layout(self, document_type: str) -> None:
        for name in ("headerState", "visibleKeys", "activePreset"):
            self._remove(document_type, name)
