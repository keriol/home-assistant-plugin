import httpx

from wilfred import (
    ExecutionRequest,
    ReadActionVerifyRequest,
    ReadActionVerifyWorkflow,
    ToolRegistry,
    VerificationStatus,
)
from wilfred.plugins import load_plugins

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
    load_plugins(
        registry,
        [create_plugin(config, client=client)],
    )

    return registry


def workflow_request() -> ReadActionVerifyRequest:
    return ReadActionVerifyRequest(
        read_before=ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        ),
        action=ExecutionRequest(
            tool_name="home_assistant_call_action",
            arguments={
                "action": "turn_on",
                "target": "desk_light",
            },
            confirmed=True,
        ),
        read_after=ExecutionRequest(
            tool_name="home_assistant_get_state",
            arguments={"target": "desk_light"},
        ),
        verifier=lambda before, _action, after: (
            before["state"] == "off"
            and after["state"] == "on"
        ),
    )


def test_real_observed_change_is_verified() -> None:
    result = ReadActionVerifyWorkflow(
        configured_registry(apply_action=True)
    ).execute(workflow_request())

    assert result.status is VerificationStatus.VERIFIED
    assert result.ok


def test_successful_dispatch_without_state_change_fails() -> None:
    result = ReadActionVerifyWorkflow(
        configured_registry(apply_action=False)
    ).execute(workflow_request())

    assert result.status is VerificationStatus.FAILED
    assert result.error_code == "verification_failed"
    assert result.action is not None
    assert result.action.ok
