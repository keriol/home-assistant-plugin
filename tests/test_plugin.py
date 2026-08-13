import json

import httpx

from wilfred import (
    ExecutionEngine,
    ExecutionRequest,
    ExecutionStatus,
    ToolPermission,
    ToolRegistry,
)
from wilfred.plugins import load_plugins

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantClient,
    HomeAssistantConfig,
    create_plugin,
)


def build():
    state = {"value": "off"}

    def handler(request: httpx.Request) -> httpx.Response:
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

    registry = ToolRegistry()
    load_plugins(
        registry,
        [create_plugin(config, client=client)],
    )

    return registry


def test_plugin_registers_read_and_action_tools() -> None:
    registry = build()

    read = registry.get("home_assistant_get_state")
    action = registry.get("home_assistant_call_action")

    assert read is not None
    assert action is not None
    assert read.permission is ToolPermission.READ
    assert action.permission is ToolPermission.ACTION


def test_read_executes_without_confirmation() -> None:
    result = ExecutionEngine(build()).execute(
        ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        )
    )

    assert result.ok
    assert result.value["state"] == "off"


def test_action_requires_confirmation() -> None:
    result = ExecutionEngine(build()).execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={
                "action": "turn_on",
                "target": "desk_light",
            },
        )
    )

    assert result.status is ExecutionStatus.CONFIRMATION_REQUIRED


def test_confirmed_action_dispatches() -> None:
    result = ExecutionEngine(build()).execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={
                "action": "turn_on",
                "target": "desk_light",
            },
            confirmed=True,
        )
    )

    assert result.ok
    assert result.value["accepted"] is True
