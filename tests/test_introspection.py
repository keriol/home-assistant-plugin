import httpx

from butler_core import ExecutionEngine, ExecutionRequest, ToolPermission, ToolRegistry

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantClient,
    HomeAssistantConfig,
    create_plugin,
)
from wilfred_home_assistant.discovery import HomeAssistantDiscoveryClient
from wilfred_home_assistant.introspection import HomeAssistantIntrospector


def build():
    config = HomeAssistantConfig(
        base_url="https://ha.example",
        token="secret-token",
        targets={"desk_light": "light.demo_desk"},
        actions={
            "turn_on": HomeAssistantAction(
                domain="light",
                service="turn_on",
            ),
            "forbidden_here": HomeAssistantAction(
                domain="cover",
                service="open_cover",
            ),
        },
    )

    def http_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/":
            return httpx.Response(200, json={"message": "API running."})
        if request.url.path == "/api/states/light.demo_desk":
            return httpx.Response(
                200,
                json={
                    "entity_id": "light.demo_desk",
                    "state": "on",
                    "attributes": {
                        "friendly_name": "Demo desk",
                        "brightness": 123,
                    },
                },
            )
        return httpx.Response(404, json={})

    def command(command_type: str, payload: dict[str, object]) -> object:
        if command_type == "config/entity_registry/list_for_display":
            return {
                "entities": [
                    {
                        "ei": "light.demo_desk",
                        "pl": "demo",
                        "ai": "office",
                        "di": "device-demo-1",
                        "en": "Demo desk",
                    },
                    {
                        "ei": "sensor.discovered_only",
                        "pl": "demo",
                        "en": "Discovered only",
                    },
                ]
            }
        if command_type == "get_services_for_target":
            entity_ids = payload["target"]["entity_id"]  # type: ignore[index]
            if entity_ids == ["light.demo_desk"]:
                return ["light.turn_off", "light.turn_on"]
            return []
        raise AssertionError(command_type)

    client = HomeAssistantClient(
        config,
        transport=httpx.MockTransport(http_handler),
    )
    discovery = HomeAssistantDiscoveryClient(
        config,
        command_transport=command,
    )
    return config, client, discovery


def test_resource_inspection_keeps_provider_and_authorization_facts_separate() -> None:
    config, client, discovery = build()
    introspector = HomeAssistantIntrospector(config, client, discovery)

    mapped = introspector.inspect_entity("light.demo_desk")
    discovered_only = introspector.inspect_entity("sensor.discovered_only")

    assert mapped.exists is True
    assert mapped.state is not None
    assert mapped.state["state"] == "on"
    assert mapped.provider_actions == ("light.turn_off", "light.turn_on")
    assert mapped.mapped_targets == ("desk_light",)
    assert mapped.authorized is True

    assert discovered_only.exists is True
    assert discovered_only.mapped_targets == ()
    assert discovered_only.authorized is False


def test_mapping_validation_distinguishes_missing_mapping_and_provider_support() -> None:
    config, client, discovery = build()
    introspector = HomeAssistantIntrospector(config, client, discovery)

    missing = introspector.validate_mapping("unknown_target")
    valid = introspector.validate_mapping("desk_light", "turn_on")
    unsupported = introspector.validate_mapping("desk_light", "forbidden_here")
    unauthorized_action = introspector.validate_mapping("desk_light", "not_configured")

    assert missing.reason_code == "target_not_mapped"
    assert missing.valid is False

    assert valid.provider_exists is True
    assert valid.provider_supports_action is True
    assert valid.authorized is True
    assert valid.valid is True

    assert unsupported.provider_exists is True
    assert unsupported.provider_supports_action is False
    assert unsupported.authorized is False
    assert unsupported.reason_code == "provider_action_not_applicable"

    assert unauthorized_action.provider_exists is True
    assert unauthorized_action.provider_supports_action is None
    assert unauthorized_action.authorized is False
    assert unauthorized_action.reason_code == "action_not_authorized"


def test_plugin_exposes_introspection_as_read_only_core_tools() -> None:
    config, client, discovery = build()
    plugin = create_plugin(config, client=client, discovery=discovery)
    registry = ToolRegistry()
    plugin.register(registry)

    names = {
        "home_assistant_entity_exists",
        "home_assistant_describe_entity",
        "home_assistant_list_entity_actions",
        "home_assistant_validate_mapping",
    }
    for name in names:
        tool = registry.get(name)
        assert tool is not None
        assert tool.permission is ToolPermission.READ

    engine = ExecutionEngine(registry)
    exists = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_entity_exists",
            arguments={"entity_id": "sensor.discovered_only"},
        )
    )
    describe = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_describe_entity",
            arguments={"entity_id": "light.demo_desk"},
        )
    )
    validation = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_validate_mapping",
            arguments={"target": "desk_light", "action": "turn_on"},
        )
    )

    assert exists.ok and exists.value["exists"] is True
    assert describe.ok and describe.value["authorized"] is True
    assert validation.ok and validation.value["valid"] is True
