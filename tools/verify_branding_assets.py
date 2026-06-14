from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "alrajhi_client" / "assets" / "brand" / "app.ico"
LOGO = ROOT / "alrajhi_client" / "assets" / "brand" / "logo.png"
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows-installer.yml"
ISS = ROOT / "build" / "setup.iss"


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def main() -> None:
    for path in (ICON, LOGO):
        if not path.exists():
            fail(f"Missing branding asset: {path.relative_to(ROOT)}")
        if path.stat().st_size < 1000:
            fail(f"Branding asset looks too small/corrupt: {path.relative_to(ROOT)}")

    data = ICON.read_bytes()
    if not data.startswith(b"\x00\x00\x01\x00"):
        fail("app.ico is not a valid Windows ICO file")
    count = int.from_bytes(data[4:6], "little")
    if count < 4:
        fail(f"app.ico should contain multiple icon sizes; found {count}")

    if WORKFLOW.exists():
        w = WORKFLOW.read_text(encoding="utf-8", errors="ignore")
        required = [
            "--icon",
            "assets\\brand\\app.ico",
            "SetupIconFile",
            "IconFilename",
        ]
        missing = [x for x in required if x not in w]
        if missing:
            fail(f"Workflow does not wire branding completely: missing {missing}")

    if ISS.exists():
        s = ISS.read_text(encoding="utf-8", errors="ignore")
        required = ["SetupIconFile", "app.ico", "IconFilename"]
        missing = [x for x in required if x not in s]
        if missing:
            fail(f"Inno setup script missing icon wiring: {missing}")

    print("OK: branding assets and build icon wiring look valid")


if __name__ == "__main__":
    main()
