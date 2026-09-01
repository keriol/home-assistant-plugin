from wilfred_home_assistant.config import HomeAssistantConnectionConfig
from wilfred_home_assistant.discovery import (
    ENTITY_REGISTRY_DISPLAY_COMMAND,
    SERVICES_FOR_TARGET_COMMAND,
    HomeAssistantDiscoveryClient,
)


def test_discovery_normalizes_native_entity_registry_metadata() -> None:
    commands: list[tuple[str, dict[str, object]]] = []

    def command(command_type: str, payload: dict[str, object]) -> object:
        commands.append((command_type, payload))
        return {
            "entities": [
                {
                    "ei": "sensor.demo_temperature",
                    "pl": "demo",
                    "ai": "office",
                    "di": "device-demo-1",
                    "en": "Demo temperature",
                    "lb": ["climate"],
                },
                {
                    "ei": "light.demo_desk",
                    "pl": "demo",
                    "en": "Demo desk",
                },
            ]
        }

    client = HomeAssistantDiscoveryClient(
        HomeAssistantConnectionConfig(
            base_url="https://ha.example",
            token="secret-token",
        ),
        command_transport=command,
    )

    discovered = client.discover_entities()

    assert commands == [(ENTITY_REGISTRY_DISPLAY_COMMAND, {})]
    assert [item.entity_id for item in discovered] == [
        "light.demo_desk",
        "sensor.demo_temperature",
    ]
    sensor = discovered[1]
    assert sensor.domain == "sensor"
    assert sensor.area_id == "office"
    assert sensor.device_id == "device-demo-1"
    assert sensor.labels == ("climate",)
    assert "secret-token" not in repr(discovered)


def test_discovery_is_not_an_authorization_mapping() -> None:
    client = HomeAssistantDiscoveryClient(
        HomeAssistantConnectionConfig(
            base_url="https://ha.example",
            token="secret-token",
        ),
        command_transport=lambda _command, _payload: {
            "entities": [
                {
                    "ei": "switch.discovered_only",
                    "pl": "demo",
                }
            ]
        },
    )

    discovered = client.discover_entities()[0].to_dict()

    assert discovered["entity_id"] == "switch.discovered_only"
    assert "authorized" not in discovered
    assert "action" not in discovered
    assert "service" not in discovered


def test_provider_actions_are_queried_for_specific_target() -> None:
    commands: list[tuple[str, dict[str, object]]] = []

    def command(command_type: str, payload: dict[str, object]) -> object:
        commands.append((command_type, payload))
        return ["light.turn_off", "light.turn_on", "light.turn_on"]

    client = HomeAssistantDiscoveryClient(
        HomeAssistantConnectionConfig(
            base_url="https://ha.example",
            token="secret-token",
        ),
        command_transport=command,
    )

    services = client.services_for_entity("light.demo_desk")

    assert services == ("light.turn_off", "light.turn_on")
    assert commands == [
        (
            SERVICES_FOR_TARGET_COMMAND,
            {
                "target": {"entity_id": ["light.demo_desk"]},
                "expand_group": False,
            },
        )
    ]
