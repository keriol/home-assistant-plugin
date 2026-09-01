from wilfred_home_assistant.config import HomeAssistantConnectionConfig
from wilfred_home_assistant.discovery import (
    ENTITY_REGISTRY_DISPLAY_COMMAND,
    HomeAssistantDiscoveryClient,
)


def test_discovery_normalizes_native_entity_registry_metadata() -> None:
    commands: list[str] = []

    def command(command_type: str) -> object:
        commands.append(command_type)
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

    assert commands == [ENTITY_REGISTRY_DISPLAY_COMMAND]
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
        command_transport=lambda _: {
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
