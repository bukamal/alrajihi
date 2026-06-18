# -*- coding: utf-8 -*-
"""Tabbed shell foundation for the Alrajhi desktop client."""
from .tab_workspace import TabbedWorkspace
from .tab_registry import TabDescriptor, TabRegistry
from .quick_open_dialog import QuickOpenDialog, QuickOpenItem
from .workspace_state import WorkspaceEntry, WorkspaceStateStore

__all__ = ["TabbedWorkspace", "TabDescriptor", "TabRegistry", "QuickOpenDialog", "QuickOpenItem", "WorkspaceEntry", "WorkspaceStateStore", "UnifiedActionBar", "NotificationCenter", "NotificationItem"]

from .unified_action_bar import UnifiedActionBar

from .notification_center import NotificationCenter, NotificationItem
