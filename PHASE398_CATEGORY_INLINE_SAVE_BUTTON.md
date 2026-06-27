# Phase 398 — Category Inline Save Button Hotfix

## Problem

When adding a new category from the Categories workspace, the editor opens inline. The generic inline document layout hides duplicate document header cards. The category editor kept its only Save button inside that hidden header card, so inline category creation had no visible Save command.

## Fix

The category editor now provides a dedicated inline action bar outside the hidden header surface. The bar contains a Save button connected to the same `workspace_save()` command as the standalone header button.

## Runtime contract

- Standalone category documents keep the existing header Save button.
- Inline category documents hide the duplicate header but show `CategoryInlineActionBar`.
- The inline Save button respects the same create/edit permission state.
- Saving still emits `saved`, refreshes the category list, and closes the inline editor through the existing inline host lifecycle.
