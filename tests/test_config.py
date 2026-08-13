import pytest

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantConfig,
    HomeAssistantConfigurationError,
)


def config() -> HomeAssistantConfig:
    return HomeAssistantConfig(
        base_url="http://ha.example:8123/",
        token="secret-token",
        targets={
            "desk_light": "light.demo_desk",
        },
        actions={
            "turn_on": HomeAssistantAction(
                domain="light",
                service="turn_on",
            ),
        },
    )


def test_configuration_normalizes_url() -> None:
    resolved = config()

    assert resolved.base_url == "http://ha.example:8123"
    assert resolved.resolve_target("desk_light") == "light.demo_desk"
    assert resolved.resolve_action("turn_on").service == "turn_on"
    assert "secret-token" not in repr(resolved)


def test_environment_configuration() -> None:
    resolved = HomeAssistantConfig.from_environment(
        targets={"desk_light": "light.demo_desk"},
        actions={
            "turn_on": HomeAssistantAction(
                domain="light",
                service="turn_on",
            )
        },
        environ={
            "WILFRED_HOME_ASSISTANT_URL": "https://ha.example",
            "WILFRED_HOME_ASSISTANT_TOKEN": "token",
        },
    )

    assert resolved.base_url == "https://ha.example"


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "ha.example",
        "ftp://ha.example",
        "https://ha.example/path",
    ],
)
def test_invalid_url_rejected(base_url: str) -> None:
    with pytest.raises(HomeAssistantConfigurationError):
        HomeAssistantConfig(
            base_url=base_url,
            token="token",
            targets={"desk_light": "light.demo_desk"},
            actions={
                "turn_on": HomeAssistantAction(
                    domain="light",
                    service="turn_on",
                )
            },
        )


def test_action_defaults_cannot_override_target() -> None:
    with pytest.raises(
        HomeAssistantConfigurationError,
        match="cannot override target",
    ):
        HomeAssistantAction(
            domain="light",
            service="turn_on",
            data={"entity_id": "light.forbidden"},
        )
