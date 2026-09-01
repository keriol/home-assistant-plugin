import httpx

from butler_core import ExecutionEngine, ExecutionRequest, ToolRegistry

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantClient,
    HomeAssistantConfig,
    create_plugin,
)


def configured_registry(*, apply_action: bool) -> ToolRegistry:
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

        if apply_action:
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
    create_plugin(config, client=client).register(registry)
    return registry


def execute_read_action_read(*, apply_action: bool) -> tuple[str, bool, str]:
    engine = ExecutionEngine(configured_registry(apply_action=apply_action))

    before = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        )
    )
    action = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={"action": "turn_on", "target": "desk_light"},
            confirmed=True,
        )
    )
    after = engine.execute(
        ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        )
    )

    assert before.ok
    assert action.ok
    assert after.ok
    return before.value["state"], action.ok, after.value["state"]


def test_real_observed_change_is_verifiable() -> None:
    before, action_ok, after = execute_read_action_read(apply_action=True)
    assert action_ok
    assert before == "off"
    assert after == "on"


def test_successful_dispatch_without_state_change_is_not_verified() -> None:
    before, action_ok, after = execute_read_action_read(apply_action=False)
    assert action_ok
    assert before == "off"
    assert after == "off"
