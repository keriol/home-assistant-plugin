import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "wilfred_home_assistant"

ENTITY_ID = re.compile(
    r"^[a-z0-9_]+\.[a-z0-9_]+$"
)


def python_string_literals():
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    yield path, node.value


def test_no_environment_file_is_committed() -> None:
    assert not (ROOT / ".env").exists()


def test_package_has_no_hardcoded_entity_ids() -> None:
    found = []

    for path, value in python_string_literals():
        if ENTITY_ID.fullmatch(value):
            found.append(
                (
                    path.relative_to(ROOT),
                    value,
                )
            )

    assert found == []


def test_package_has_no_hardcoded_server_urls() -> None:
    found = []

    for path, value in python_string_literals():
        if value.startswith(
            (
                "http://",
                "https://",
            )
        ):
            found.append(
                (
                    path.relative_to(ROOT),
                    value,
                )
            )

    assert found == []
