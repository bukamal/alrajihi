import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "alrajhi_client") not in sys.path:
    sys.path.insert(0, str(ROOT / "alrajhi_client"))


def test_phase20_translations_exist():
    from alrajhi_client.i18n import translator
    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        assert translator.translate("restaurant.dashboard") != "restaurant.dashboard"
        assert translator.translate("industry.restaurant") != "industry.restaurant"


def test_server_http_layers_have_no_sql_literals():
    forbidden_roots = [ROOT / "alrajhi_server" / "api", ROOT / "alrajhi_server" / "services" / "http_routes"]
    sql_keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "PRAGMA")
    offenders = []
    for base in forbidden_roots:
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    text = " ".join(node.value.upper().split())
                    if any(text.startswith(keyword + " ") for keyword in sql_keywords):
                        offenders.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}")
    assert offenders == []


def test_phase20_no_legacy_sql_repository_dependency():
    offenders = []
    for path in (ROOT / "alrajhi_server").rglob("*.py"):
        if "LegacySqlRepository" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
