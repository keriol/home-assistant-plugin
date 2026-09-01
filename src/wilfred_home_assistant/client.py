from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from wilfred_home_assistant.config import HomeAssistantConfig
from wilfred_home_assistant.errors import (
    HomeAssistantConnectionError,
    HomeAssistantNotFoundError,
    HomeAssistantResponseError,
    HomeAssistantUnauthorizedError,
    HomeAssistantUnavailableError,
)


@dataclass(frozen=True)
class HomeAssistantState:
    entity_id: str
    state: str
    attributes: dict[str, Any]
    last_changed: str | None = None
    last_updated: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "state": self.state,
            "attributes": dict(self.attributes),
            "last_changed": self.last_changed,
            "last_updated": self.last_updated,
        }


class HomeAssistantClient:
    """Small synchronous client for the Home Assistant REST API."""

    def __init__(
        self,
        config: HomeAssistantConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.token}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HomeAssistantClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            response = self._client.request(method, path, json=json)
        except httpx.HTTPError as exc:
            raise HomeAssistantConnectionError(
                "Cannot connect to Home Assistant."
            ) from exc

        if response.status_code == 401:
            raise HomeAssistantUnauthorizedError(
                "Home Assistant rejected the configured credential."
            )
        if response.status_code == 404:
            raise HomeAssistantNotFoundError(
                "Home Assistant resource was not found."
            )
        if response.is_error:
            raise HomeAssistantResponseError(
                "Home Assistant returned HTTP "
                f"{response.status_code}."
            )
        return response

    @staticmethod
    def _json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise HomeAssistantResponseError(
                "Home Assistant returned invalid JSON."
            ) from exc

    def check_api(self) -> None:
        """Perform a READ-only API readiness check."""
        payload = self._json(self._request("GET", "/api/"))
        if not isinstance(payload, dict):
            raise HomeAssistantResponseError(
                "Home Assistant API readiness response must be an object."
            )

    def get_state(self, entity_id: str) -> HomeAssistantState:
        encoded = quote(entity_id, safe="._-")
        response = self._request("GET", f"/api/states/{encoded}")
        payload = self._json(response)
        if not isinstance(payload, dict):
            raise HomeAssistantResponseError(
                "Home Assistant state response must be an object."
            )
        state = payload.get("state")
        returned_entity_id = payload.get("entity_id")
        attributes = payload.get("attributes", {})
        if (
            not isinstance(state, str)
            or not isinstance(returned_entity_id, str)
            or not isinstance(attributes, dict)
        ):
            raise HomeAssistantResponseError(
                "Home Assistant returned an invalid state object."
            )
        if state == "unavailable":
            raise HomeAssistantUnavailableError(
                f"Home Assistant entity {returned_entity_id!r} is unavailable."
            )
        return HomeAssistantState(
            entity_id=returned_entity_id,
            state=state,
            attributes=dict(attributes),
            last_changed=payload.get("last_changed"),
            last_updated=payload.get("last_updated"),
        )

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/services/{quote(domain, safe='_')}/{quote(service, safe='_')}",
            json=service_data,
        )
        payload = self._json(response)
        if not isinstance(payload, (list, dict)):
            raise HomeAssistantResponseError(
                "Home Assistant service response must be a list or object."
            )
        return {"accepted": True, "response": payload}
