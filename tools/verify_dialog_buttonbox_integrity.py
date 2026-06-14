#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD_PATTERNS = [
    "buttons = QDialogButtonBox, QMenu",
    "QMenu.Save",
    "QMenu.Cancel",
    "QMenu.Ok",
    "QMenu.Open",
]

def main():
    bad = []
    for path in (ROOT / "alrajhi_client").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in BAD_PATTERNS:
            if pattern in text:
                bad.append((path.relative_to(ROOT), pattern))
    if bad:
        for path, pattern in bad:
            print(f"BAD_DIALOG_BUTTONBOX_PATTERN {path}: {pattern}")
        raise SystemExit(1)
    print("dialog buttonbox integrity ok")

if __name__ == "__main__":
    main()
