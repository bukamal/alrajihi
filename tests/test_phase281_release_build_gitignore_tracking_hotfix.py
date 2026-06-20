from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _gitignore_lines() -> set[str]:
    return {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def test_release_build_files_are_present_and_trackable():
    required_files = [
        ROOT / "build" / "build_windows.ps1",
        ROOT / "build" / "setup.iss",
        ROOT / "build" / "pyinstaller_hidden_imports.py",
        ROOT / "build" / "hooks" / "hook-printing.py",
        ROOT / "build" / "hooks" / "hook-alrajhi_client.printing.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    assert missing == []

    lines = _gitignore_lines()
    assert "build/" not in lines
    for pattern in (
        "build/*",
        "!build/",
        "!build/build_windows.ps1",
        "!build/setup.iss",
        "!build/pyinstaller_hidden_imports.py",
        "!build/hooks/",
        "!build/hooks/*.py",
    ):
        assert pattern in lines


def test_windows_packaging_gate_checks_gitignore_tracking():
    from alrajhi_client.workspace.packaging.windows_packaging_gate_contract import (
        REQUIRED_GITIGNORE_BUILD_TRACKING,
        validate_windows_packaging_gate,
        windows_packaging_gate_summary,
    )

    assert "!build/pyinstaller_hidden_imports.py" in REQUIRED_GITIGNORE_BUILD_TRACKING
    assert "!build/hooks/*.py" in REQUIRED_GITIGNORE_BUILD_TRACKING
    assert validate_windows_packaging_gate(ROOT) == {}
    assert windows_packaging_gate_summary(ROOT)["ready"] is True
