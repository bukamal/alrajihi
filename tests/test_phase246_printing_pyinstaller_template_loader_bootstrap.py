from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_printing_service_does_not_startup_crash_on_missing_template_loader():
    text = read("alrajhi_client/printing/printing_service.py")
    assert "from ._template_loader import require_template" not in text
    assert "_import_runtime_require_template" in text
    assert "_local_require_template" in text
    assert "PRINT-TEMPLATE-BOOTSTRAP-UNAVAILABLE" in text


def test_print_manager_no_longer_imports_template_loader_at_module_import_time():
    text = read("alrajhi_client/printing/print_manager.py")
    assert "from ._template_loader import require_template" not in text
    assert "from .printing_service import invoice_html" in text


def test_windows_build_packages_template_loader_as_hidden_import_and_data():
    workflow = read(".github/workflows/build-windows-installer.yml")
    ps1 = read("build/build_windows.ps1")
    manifest = read("build/pyinstaller_hidden_imports.py")

    assert r"build\build_windows.ps1" in workflow or '"--hidden-import", "printing._template_loader"' in workflow
    assert "--hidden-import printing._template_loader" in ps1
    assert "--hidden-import alrajhi_client.printing._template_loader" in ps1
    assert '"printing._template_loader"' in manifest
    assert '"alrajhi_client.printing._template_loader"' in manifest

    assert r"build\build_windows.ps1" in workflow or "alrajhi_client\\printing\\_template_loader.py;printing" in workflow
    assert "alrajhi_client\\printing\\_template_loader.py;printing" in ps1
    assert "alrajhi_client\\printing\\_template_loader.py;alrajhi_client\\printing" in ps1


def test_phase225_guard_protects_template_loader_contract():
    text = read("tools/phase225_printing_pyinstaller_guard.py")
    assert "printing._template_loader" in text
    assert "_template_loader.py;printing" in text
