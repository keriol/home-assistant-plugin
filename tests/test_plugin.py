import json

import httpx

from butler_core import (
    AvailabilityState,
    ExecutionEngine,
    ExecutionRequest,
    ExecutionStatus,
    ToolPermission,
    ToolRegistry,
    evaluate_availability_probe,
    validate_plugin_definition,
)

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantClient,
    HomeAssistantConfig,
    HomeAssistantTarget,
    create_plugin,
)


def build(*, api_status: int = 200):
    state = {"value": "off"}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/":
            return httpx.Response(api_status, json={"message": "API running."})

        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "entity_id": "light.demo_desk",
                    "state": state["value"],
                    "attributes": {},
                },
            )

        payload = json.loads(request.content)
        assert payload["entity_id"] == "light.demo_desk"
        state["value"] = "on"
        return httpx.Response(200, json=[])

    config = HomeAssistantConfig(
        base_url="http://ha.example:8123",
        token="token",
        targets={"desk_light": "light.demo_desk"},
        actions={
            "turn_on": HomeAssistantAction(
                domain="light",
                service="turn_on",
            )
        },
    )

    client = HomeAssistantClient(
        config,
        transport=httpx.MockTransport(handler),
    )
    plugin = create_plugin(config, client=client)
    registry = ToolRegistry()
    plugin.register(registry)
    return registry, plugin


def test_plugin_declares_home_capabilities_through_core() -> None:
    _registry, plugin = build()

    assert [domain.identity for domain in plugin.domains] == ["home"]
    assert [capability.identity for capability in plugin.capabilities] == [
        "home.control",
        "home.state",
    ]
    validate_plugin_definition(plugin)


def test_plugin_registers_read_and_action_tools() -> None:
    registry, _plugin = build()
    read = registry.get("home_assistant_get_state")
    action = registry.get("home_assistant_call_action")

    assert read is not None
    assert action is not None
    assert read.permission is ToolPermission.READ
    assert action.permission is ToolPermission.ACTION


def test_read_executes_without_confirmation() -> None:
    registry, _plugin = build()
    result = ExecutionEngine(registry).execute(
        ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        )
    )
    assert result.ok
    assert result.value["state"] == "off"


def test_action_requires_confirmation() -> None:
    registry, _plugin = build()
    result = ExecutionEngine(registry).execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={"action": "turn_on", "target": "desk_light"},
        )
    )
    assert result.status is ExecutionStatus.CONFIRMATION_REQUIRED


def test_confirmed_action_dispatches() -> None:
    registry, _plugin = build()
    result = ExecutionEngine(registry).execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={"action": "turn_on", "target": "desk_light"},
            confirmed=True,
        )
    )
    assert result.ok
    assert result.value["accepted"] is True


def test_plugin_and_capabilities_report_usable_readiness() -> None:
    _registry, plugin = build()

    plugin_result = evaluate_availability_probe(plugin.readiness_probe)
    assert plugin_result.state is AvailabilityState.USABLE

    assert {
        evaluate_availability_probe(capability.availability_probe).state
        for capability in plugin.capabilities
    } == {AvailabilityState.USABLE}


def test_authentication_failure_is_structured_unavailable() -> None:
    _registry, plugin = build(api_status=401)

    result = evaluate_availability_probe(plugin.readiness_probe)
    assert result.state is AvailabilityState.UNAVAILABLE
    assert result.reason_code == "home_assistant_authentication_failed"


def test_confirmed_action_can_dispatch_to_authorized_device_id() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/":
            return httpx.Response(200, json={"message": "API running."})
        payload = json.loads(request.content)
        observed["payload"] = payload
        return httpx.Response(200, json=[])

    config = HomeAssistantConfig(
        base_url="http://ha.example:8123",
        token="token",
        targets={"tv_remote": HomeAssistantTarget(device_id="device-demo-tv")},
        actions={"turn_on": HomeAssistantAction(domain="remote", service="turn_on")},
    )
    client = HomeAssistantClient(config, transport=httpx.MockTransport(handler))
    plugin = create_plugin(config, client=client)
    registry = ToolRegistry()
    plugin.register(registry)

    result = ExecutionEngine(registry).execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={"action": "turn_on", "target": "tv_remote"},
            confirmed=True,
        )
    )

    assert result.ok
    assert observed["payload"] == {"device_id": "device-demo-tv"}

    read_tool = registry.get("home_assistant_get_state")
    action_tool = registry.get("home_assistant_call_action")
    assert read_tool is not None
    assert action_tool is not None
    assert read_tool.parameters["properties"]["target"]["enum"] == []
    assert action_tool.parameters["properties"]["target"]["enum"] == ["tv_remote"]
