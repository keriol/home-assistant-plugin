from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import os
import re
from typing import Any
from urllib.parse import urlsplit

from wilfred_home_assistant.errors import (
    HomeAssistantConfigurationError,
)


_NAME = re.compile(r"[a-z][a-z0-9_-]*")
_ENTITY_ID = re.compile(r"[a-z0-9_]+\.[a-z0-9_]+")
_SERVICE = re.compile(r"[a-z0-9_]+")
_RESERVED_TARGET_KEYS = frozenset(
    {
        "area_id",
        "device_id",
        "entity_id",
        "target",
    }
)


def _logical_name(value: str, *, kind: str) -> str:
    normalized = value.strip()

    if _NAME.fullmatch(normalized) is None:
        raise HomeAssistantConfigurationError(
            f"Invalid {kind} name: {value!r}."
        )

    return normalized


@dataclass(frozen=True)
class HomeAssistantAction:
    domain: str
    service: str
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        domain = self.domain.strip()
        service = self.service.strip()

        if _SERVICE.fullmatch(domain) is None:
            raise HomeAssistantConfigurationError(
                f"Invalid Home Assistant domain: {self.domain!r}."
            )

        if _SERVICE.fullmatch(service) is None:
            raise HomeAssistantConfigurationError(
                f"Invalid Home Assistant service: {self.service!r}."
            )

        forbidden = sorted(
            _RESERVED_TARGET_KEYS.intersection(self.data)
        )

        if forbidden:
            raise HomeAssistantConfigurationError(
                "Action defaults cannot override target fields: "
                + ", ".join(forbidden)
                + "."
            )


@dataclass(frozen=True)
class HomeAssistantConfig:
    base_url: str
    token: str = field(repr=False)
    targets: Mapping[str, str] = field(default_factory=dict)
    actions: Mapping[str, HomeAssistantAction] = field(default_factory=dict)
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        base_url = self.base_url.strip().rstrip("/")
        token = self.token.strip()

        parsed = urlsplit(base_url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise HomeAssistantConfigurationError(
                "Home Assistant URL must be an absolute http/https URL."
            )

        if parsed.query or parsed.fragment:
            raise HomeAssistantConfigurationError(
                "Home Assistant URL cannot contain query or fragment."
            )

        if parsed.path not in {"", "/"}:
            raise HomeAssistantConfigurationError(
                "Home Assistant URL must point to the server root."
            )

        if not token:
            raise HomeAssistantConfigurationError(
                "Home Assistant token cannot be empty."
            )

        if self.timeout_seconds <= 0:
            raise HomeAssistantConfigurationError(
                "Home Assistant timeout must be greater than zero."
            )

        if not self.targets:
            raise HomeAssistantConfigurationError(
                "At least one logical Home Assistant target is required."
            )

        if not self.actions:
            raise HomeAssistantConfigurationError(
                "At least one authorized Home Assistant action is required."
            )

        normalized_targets: dict[str, str] = {}

        for name, entity_id in self.targets.items():
            logical = _logical_name(name, kind="target")
            entity = entity_id.strip()

            if _ENTITY_ID.fullmatch(entity) is None:
                raise HomeAssistantConfigurationError(
                    f"Invalid entity_id for target {logical!r}: {entity_id!r}."
                )

            normalized_targets[logical] = entity

        normalized_actions: dict[str, HomeAssistantAction] = {}

        for name, action in self.actions.items():
            logical = _logical_name(name, kind="action")

            if not isinstance(action, HomeAssistantAction):
                raise HomeAssistantConfigurationError(
                    f"Action {logical!r} must be HomeAssistantAction."
                )

            normalized_actions[logical] = action

        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "token", token)
        object.__setattr__(self, "targets", normalized_targets)
        object.__setattr__(self, "actions", normalized_actions)

    @classmethod
    def from_environment(
        cls,
        *,
        targets: Mapping[str, str],
        actions: Mapping[str, HomeAssistantAction],
        environ: Mapping[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> "HomeAssistantConfig":
        values = os.environ if environ is None else environ

        try:
            base_url = values["WILFRED_HOME_ASSISTANT_URL"]
            token = values["WILFRED_HOME_ASSISTANT_TOKEN"]
        except KeyError as exc:
            raise HomeAssistantConfigurationError(
                f"Missing environment variable: {exc.args[0]}."
            ) from exc

        return cls(
            base_url=base_url,
            token=token,
            targets=targets,
            actions=actions,
            timeout_seconds=timeout_seconds,
        )

    def resolve_target(self, name: str) -> str:
        try:
            return self.targets[name]
        except KeyError as exc:
            raise HomeAssistantConfigurationError(
                f"Unknown Home Assistant target: {name!r}."
            ) from exc

    def resolve_action(self, name: str) -> HomeAssistantAction:
        try:
            return self.actions[name]
        except KeyError as exc:
            raise HomeAssistantConfigurationError(
                f"Unknown Home Assistant action: {name!r}."
            ) from exc


def reject_target_override(data: Mapping[str, Any]) -> None:
    forbidden = sorted(
        _RESERVED_TARGET_KEYS.intersection(data)
    )

    if forbidden:
        raise HomeAssistantConfigurationError(
            "Action data cannot override configured target fields: "
            + ", ".join(forbidden)
            + "."
        )
