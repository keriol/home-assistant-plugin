import ast
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "wilfred_home_assistant"

ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


def python_string_literals():
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield path, node.value


def test_no_environment_file_is_committed() -> None:
    assert not (ROOT / ".env").exists()


def test_runtime_source_has_no_wilfred_imports() -> None:
    found = []
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "wilfred" or alias.name.startswith("wilfred."):
                        found.append((path.relative_to(ROOT), alias.name))
            if module == "wilfred" or (module and module.startswith("wilfred.")):
                found.append((path.relative_to(ROOT), module))

    assert found == []


def test_distribution_has_no_wilfred_runtime_dependency() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    assert project["name"] == "butler-home-assistant"
    assert project["version"] == "0.2.0.dev0"
    assert any(str(dep).startswith("butler-core") for dep in project["dependencies"])
    assert all("wilfred-butler" not in str(dep) for dep in project["dependencies"])


def test_package_has_no_hardcoded_entity_ids() -> None:
    found = []
    for path, value in python_string_literals():
        if ENTITY_ID.fullmatch(value):
            found.append((path.relative_to(ROOT), value))
    assert found == []


def test_package_has_no_hardcoded_server_urls() -> None:
    found = []
    for path, value in python_string_literals():
        if value.startswith(("http://", "https://")):
            found.append((path.relative_to(ROOT), value))
    assert found == []
