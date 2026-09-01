from pathlib import Path

import pytest

from butler_core import ToolRegistry, validate_plugin_definition

from wilfred_home_assistant.bootstrap import create_plugin_from_environment
from wilfred_home_assistant.errors import HomeAssistantConfigurationError


def write_config(path: Path) -> None:
    path.write_text(
        """
[targets]
demo_light = "light.demo"

[actions.turn_on]
domain = "light"
service = "turn_on"

[actions.turn_on.data]
brightness = 100
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_factory_builds_configured_plugin(tmp_path: Path) -> None:
    config = tmp_path / "home-assistant.toml"
    write_config(config)

    plugin = create_plugin_from_environment(
        {
            "HAP_HOME_ASSISTANT_URL": "http://ha.example:8123",
            "HAP_HOME_ASSISTANT_TOKEN": "test-token",
            "HAP_HOME_ASSISTANT_CONFIG": str(config),
        }
    )

    registry = ToolRegistry()
    plugin.register(registry)
    validate_plugin_definition(plugin)

    assert plugin.name == "home-assistant"
    assert [domain.identity for domain in plugin.domains] == ["home"]
    assert [capability.identity for capability in plugin.capabilities] == [
        "home.control",
        "home.state",
    ]
    assert registry.names() == [
        "home_assistant_call_action",
        "home_assistant_describe_entity",
        "home_assistant_entity_exists",
        "home_assistant_get_state",
        "home_assistant_list_entity_actions",
        "home_assistant_validate_mapping",
    ]


def test_factory_accepts_legacy_wilfred_environment_names(tmp_path: Path) -> None:
    config = tmp_path / "home-assistant.toml"
    write_config(config)

    plugin = create_plugin_from_environment(
        {
            "WILFRED_HOME_ASSISTANT_URL": "http://ha.example:8123",
            "WILFRED_HOME_ASSISTANT_TOKEN": "test-token",
            "WILFRED_HOME_ASSISTANT_CONFIG": str(config),
        }
    )

    assert plugin.name == "home-assistant"


def test_factory_requires_canonical_config_path() -> None:
    with pytest.raises(
        HomeAssistantConfigurationError,
        match="HAP_HOME_ASSISTANT_CONFIG",
    ):
        create_plugin_from_environment(
            {
                "HAP_HOME_ASSISTANT_URL": "http://ha.example:8123",
                "HAP_HOME_ASSISTANT_TOKEN": "test-token",
            }
        )


def test_factory_rejects_unknown_sections(tmp_path: Path) -> None:
    config = tmp_path / "home-assistant.toml"
    config.write_text(
        """
[targets]
demo_light = "light.demo"

[actions.turn_on]
domain = "light"
service = "turn_on"

[private]
unexpected = true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(HomeAssistantConfigurationError, match="Unknown"):
        create_plugin_from_environment(
            {
                "HAP_HOME_ASSISTANT_URL": "http://ha.example:8123",
                "HAP_HOME_ASSISTANT_TOKEN": "test-token",
                "HAP_HOME_ASSISTANT_CONFIG": str(config),
            }
        )
