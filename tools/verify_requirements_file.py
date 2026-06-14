from __future__ import annotations

from pathlib import Path

REQUIRED = {
    "PyQt5",
    "qt-material",
    "pyqtgraph",
    "qtawesome",
    "openpyxl",
    "reportlab",
    "qrcode",
    "Pillow",
    "python-barcode",
    "cryptography",
    "requests",
    "pyserial",
    "opencv-python",
    "pyzbar",
    "Flask",
    "Flask-JWT-Extended",
    "waitress",
    "Werkzeug",
}


def package_name(line: str) -> str:
    line = line.strip()
    for sep in (">=", "==", "<=", "~=", ">", "<"):
        if sep in line:
            return line.split(sep, 1)[0].strip()
    return line


def main() -> None:
    path = Path("requirements.txt")
    if not path.exists():
        raise SystemExit("requirements.txt is missing")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    packages = {package_name(line) for line in lines if line and not line.startswith("#")}
    missing = sorted(REQUIRED - packages)
    if missing:
        raise SystemExit("requirements.txt missing packages: " + ", ".join(missing))
    print("requirements.txt check passed")


if __name__ == "__main__":
    main()
