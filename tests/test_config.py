import pytest

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantConfig,
    HomeAssistantConfigurationError,
    HomeAssistantTarget,
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


def test_typed_device_target_keeps_read_and_action_semantics_explicit() -> None:
    resolved = HomeAssistantConfig(
        base_url="http://ha.example:8123",
        token="token",
        targets={
            "tv": HomeAssistantTarget(entity_id="remote.demo_tv", device_id="device-demo-tv"),
            "action_only": HomeAssistantTarget(device_id="device-action-only"),
        },
        actions={
            "turn_on": HomeAssistantAction(domain="remote", service="turn_on"),
        },
    )

    assert resolved.resolve_target("tv") == "remote.demo_tv"
    assert resolved.resolve_action_target("tv") == {"device_id": "device-demo-tv"}
    assert resolved.resolve_action_target("action_only") == {"device_id": "device-action-only"}

    with pytest.raises(HomeAssistantConfigurationError, match="ACTION-only"):
        resolved.resolve_target("action_only")


@pytest.mark.parametrize("field", ["entity_id", "device_id", "area_id", "target"])
def test_all_target_override_fields_are_rejected(field: str) -> None:
    from wilfred_home_assistant.config import reject_target_override

    with pytest.raises(HomeAssistantConfigurationError, match="cannot override configured target fields"):
        reject_target_override({field: "forbidden"})
