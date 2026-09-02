from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from wilfred_home_assistant.config import HomeAssistantConnectionConfig
from wilfred_home_assistant.errors import (
    HomeAssistantConnectionError,
    HomeAssistantResponseError,
    HomeAssistantUnauthorizedError,
)


ENTITY_REGISTRY_DISPLAY_COMMAND = "config/entity_registry/list_for_display"
SERVICES_FOR_TARGET_COMMAND = "get_services_for_target"


@dataclass(frozen=True)
class DiscoveredHomeAssistantEntity:
    entity_id: str
    platform: str
    name: str | None = None
    area_id: str | None = None
    device_id: str | None = None
    labels: tuple[str, ...] = ()

    @property
    def domain(self) -> str:
        return self.entity_id.split(".", 1)[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "domain": self.domain,
            "platform": self.platform,
            "name": self.name,
            "area_id": self.area_id,
            "device_id": self.device_id,
            "labels": list(self.labels),
        }


def normalize_entity_registry_display(
    payload: Any,
) -> tuple[DiscoveredHomeAssistantEntity, ...]:
    if not isinstance(payload, dict):
        raise HomeAssistantResponseError(
            "Home Assistant entity discovery response must be an object."
        )
    raw_entities = payload.get("entities")
    if not isinstance(raw_entities, list):
        raise HomeAssistantResponseError(
            "Home Assistant entity discovery response is missing entities."
        )

    entities: list[DiscoveredHomeAssistantEntity] = []
    for raw in raw_entities:
        if not isinstance(raw, dict):
            raise HomeAssistantResponseError(
                "Home Assistant returned an invalid entity registry entry."
            )
        entity_id = raw.get("ei")
        platform = raw.get("pl")
        if not isinstance(entity_id, str) or not isinstance(platform, str):
            raise HomeAssistantResponseError(
                "Home Assistant entity registry entry lacks identity metadata."
            )
        labels = raw.get("lb", [])
        if not isinstance(labels, list) or not all(
            isinstance(label, str) for label in labels
        ):
            raise HomeAssistantResponseError(
                "Home Assistant entity registry labels are invalid."
            )
        entities.append(
            DiscoveredHomeAssistantEntity(
                entity_id=entity_id,
                platform=platform,
                name=raw.get("en") if isinstance(raw.get("en"), str) else None,
                area_id=raw.get("ai") if isinstance(raw.get("ai"), str) else None,
                device_id=raw.get("di") if isinstance(raw.get("di"), str) else None,
                labels=tuple(labels),
            )
        )

    return tuple(sorted(entities, key=lambda item: item.entity_id))


def normalize_services_for_target(payload: Any) -> tuple[str, ...]:
    if not isinstance(payload, list) or not all(
        isinstance(item, str) for item in payload
    ):
        raise HomeAssistantResponseError(
            "Home Assistant target action response must be a list of identifiers."
        )
    return tuple(sorted(set(payload)))


class HomeAssistantDiscoveryClient:
    """READ-only provider discovery backed by Home Assistant native metadata."""

    def __init__(
        self,
        config: HomeAssistantConnectionConfig,
        *,
        command_transport: Callable[[str, Mapping[str, Any]], Any] | None = None,
    ) -> None:
        self._config = config
        self._command_transport = command_transport

    def _websocket_url(self) -> str:
        parsed = urlsplit(self._config.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunsplit((scheme, parsed.netloc, "/api/websocket", "", ""))

    def _command(
        self,
        command_type: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        command_payload = dict(payload or {})
        if self._command_transport is not None:
            return self._command_transport(command_type, command_payload)

        try:
            with connect(
                self._websocket_url(),
                open_timeout=self._config.timeout_seconds,
                close_timeout=self._config.timeout_seconds,
            ) as websocket:
                initial = json.loads(websocket.recv())
                if initial.get("type") != "auth_required":
                    raise HomeAssistantResponseError(
                        "Home Assistant WebSocket did not request authentication."
                    )

                websocket.send(
                    json.dumps(
                        {
                            "type": "auth",
                            "access_token": self._config.token,
                        }
                    )
                )
                authenticated = json.loads(websocket.recv())
                if authenticated.get("type") == "auth_invalid":
                    raise HomeAssistantUnauthorizedError(
                        "Home Assistant rejected the configured credential."
                    )
                if authenticated.get("type") != "auth_ok":
                    raise HomeAssistantResponseError(
                        "Home Assistant WebSocket authentication response is invalid."
                    )

                request = {"id": 1, "type": command_type}
                request.update(command_payload)
                websocket.send(json.dumps(request))
                response = json.loads(websocket.recv())
        except HomeAssistantUnauthorizedError:
            raise
        except HomeAssistantResponseError:
            raise
        except (ConnectionClosed, OSError, TimeoutError, ValueError) as exc:
            raise HomeAssistantConnectionError(
                "Cannot query Home Assistant discovery metadata."
            ) from exc

        if (
            not isinstance(response, dict)
            or response.get("id") != 1
            or response.get("type") != "result"
        ):
            raise HomeAssistantResponseError(
                "Home Assistant WebSocket returned an invalid result envelope."
            )
        if response.get("success") is not True:
            raise HomeAssistantResponseError(
                "Home Assistant rejected the discovery request."
            )
        return response.get("result")

    def discover_entities(self) -> tuple[DiscoveredHomeAssistantEntity, ...]:
        return normalize_entity_registry_display(
            self._command(ENTITY_REGISTRY_DISPLAY_COMMAND)
        )

    def services_for_target(
        self,
        selector: Mapping[str, str],
    ) -> tuple[str, ...]:
        allowed = {"device_id", "entity_id"}
        keys = set(selector)

        if len(selector) != 1 or not keys.issubset(allowed):
            raise HomeAssistantResponseError(
                "Home Assistant target selector must contain exactly one "
                "authorized entity_id or device_id."
            )

        if not all(
            isinstance(value, str) and value.strip()
            for value in selector.values()
        ):
            raise HomeAssistantResponseError(
                "Home Assistant target selector values must be non-empty strings."
            )

        target = {
            key: [value]
            for key, value in selector.items()
        }

        return normalize_services_for_target(
            self._command(
                SERVICES_FOR_TARGET_COMMAND,
                {
                    "target": target,
                    "expand_group": False,
                },
            )
        )

    def services_for_entity(self, entity_id: str) -> tuple[str, ...]:
        return self.services_for_target({"entity_id": entity_id})


__all__ = [
    "DiscoveredHomeAssistantEntity",
    "ENTITY_REGISTRY_DISPLAY_COMMAND",
    "HomeAssistantDiscoveryClient",
    "SERVICES_FOR_TARGET_COMMAND",
    "normalize_entity_registry_display",
    "normalize_services_for_target",
]
