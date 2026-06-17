# GATEWAY PHASE 75 - Returns Dialog ButtonBox Hotfix

## Scope
Fixed a functional regression in `alrajhi_client/views/widgets/returns_widget.py` introduced by an unsafe replacement that mixed `QDialogButtonBox` with `QMenu`.

## Fixed
- `SalesReturnDialog` button box creation.
- `PurchaseReturnDialog` button box creation.

## Correct pattern
```python
buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
buttons.button(QDialogButtonBox.Save).setText('حفظ المرتجع')
buttons.button(QDialogButtonBox.Cancel).setText('إلغاء')
```

## Guard added
- `tools/verify_dialog_buttonbox_integrity.py`

The guard fails if invalid patterns such as `QMenu.Save`, `QMenu.Cancel`, or `buttons = QDialogButtonBox, QMenu` reappear.

## Validation
- `python3 tools/verify_dialog_buttonbox_integrity.py` ✅
- `python3 -m compileall -q alrajhi_client` ✅
