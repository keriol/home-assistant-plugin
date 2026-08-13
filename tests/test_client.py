import httpx
import pytest

from wilfred_home_assistant import (
    HomeAssistantAction,
    HomeAssistantClient,
    HomeAssistantConfig,
    HomeAssistantConnectionError,
    HomeAssistantNotFoundError,
    HomeAssistantUnauthorizedError,
    HomeAssistantUnavailableError,
)


def config() -> HomeAssistantConfig:
    return HomeAssistantConfig(
        base_url="http://ha.example:8123",
        token="test-token",
        targets={"desk_light": "light.demo_desk"},
        actions={
            "turn_on": HomeAssistantAction(
                domain="light",
                service="turn_on",
            )
        },
    )


def test_get_state_uses_bearer_auth_and_returns_attributes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/states/light.demo_desk"
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx.Response(
            200,
            json={
                "entity_id": "light.demo_desk",
                "state": "off",
                "attributes": {"friendly_name": "Demo desk"},
                "last_changed": "2026-01-01T00:00:00+00:00",
                "last_updated": "2026-01-01T00:00:00+00:00",
            },
        )

    client = HomeAssistantClient(
        config(),
        transport=httpx.MockTransport(handler),
    )

    state = client.get_state("light.demo_desk")

    assert state.state == "off"
    assert state.attributes["friendly_name"] == "Demo desk"


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, HomeAssistantUnauthorizedError),
        (404, HomeAssistantNotFoundError),
    ],
)
def test_http_errors_are_normalized(status, error) -> None:
    client = HomeAssistantClient(
        config(),
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(status)
        ),
    )

    with pytest.raises(error) as raised:
        client.get_state("light.demo_desk")

    assert raised.value.code in {
        "unauthorized",
        "not_found",
    }


def test_unavailable_state_is_normalized() -> None:
    client = HomeAssistantClient(
        config(),
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "entity_id": "light.demo_desk",
                    "state": "unavailable",
                    "attributes": {},
                },
            )
        ),
    )

    with pytest.raises(HomeAssistantUnavailableError) as raised:
        client.get_state("light.demo_desk")

    assert raised.value.code == "unavailable"


def test_connection_error_is_normalized() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            "offline",
            request=request,
        )

    client = HomeAssistantClient(
        config(),
        transport=httpx.MockTransport(fail),
    )

    with pytest.raises(HomeAssistantConnectionError) as raised:
        client.get_state("light.demo_desk")

    assert raised.value.code == "connection_error"


def test_call_service_uses_service_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/services/light/turn_on"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.content

        return httpx.Response(
            200,
            json=[],
        )

    client = HomeAssistantClient(
        config(),
        transport=httpx.MockTransport(handler),
    )

    result = client.call_service(
        "light",
        "turn_on",
        {"entity_id": "light.demo_desk"},
    )

    assert result == {
        "accepted": True,
        "response": [],
    }
