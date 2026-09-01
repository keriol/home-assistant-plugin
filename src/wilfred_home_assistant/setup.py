from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from butler_core import AvailabilityResult, AvailabilityState

from wilfred_home_assistant.config import (
    LEGACY_TOKEN_ENV,
    LEGACY_URL_ENV,
    TOKEN_ENV,
    URL_ENV,
    HomeAssistantConnectionConfig,
)
from wilfred_home_assistant.errors import HomeAssistantConfigurationError


CONFIG_ENV = "HAP_HOME_ASSISTANT_CONFIG"
LEGACY_CONFIG_ENV = "WILFRED_HOME_ASSISTANT_CONFIG"


class SetupFieldKind(str, Enum):
    TEXT = "text"
    SECRET = "secret"
    PATH = "path"
    NUMBER = "number"


@dataclass(frozen=True)
class SetupFieldDefinition:
    key: str
    label: str
    description: str
    kind: SetupFieldKind
    required: bool
    environment_variable: str | None = None
    legacy_environment_variable: str | None = None
    default: Any = None

    @property
    def secret(self) -> bool:
        return self.kind is SetupFieldKind.SECRET

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "kind": self.kind.value,
            "required": self.required,
            "secret": self.secret,
            "environment_variable": self.environment_variable,
            "legacy_environment_variable": self.legacy_environment_variable,
            "default": self.default,
        }


@dataclass(frozen=True)
class SetupDefinition:
    plugin: str
    title: str
    description: str
    fields: tuple[SetupFieldDefinition, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "plugin": self.plugin,
            "title": self.title,
            "description": self.description,
            "fields": [field.to_safe_dict() for field in self.fields],
        }


HOME_ASSISTANT_SETUP = SetupDefinition(
    plugin="home-assistant",
    title="Home Assistant",
    description=(
        "Connect the Home Assistant Plugin and provide explicit logical target "
        "and authorized-action mappings."
    ),
    fields=(
        SetupFieldDefinition(
            key="base_url",
            label="Home Assistant URL",
            description="Root HTTP or HTTPS URL of the Home Assistant server.",
            kind=SetupFieldKind.TEXT,
            required=True,
            environment_variable=URL_ENV,
            legacy_environment_variable=LEGACY_URL_ENV,
        ),
        SetupFieldDefinition(
            key="token",
            label="Access credential",
            description=(
                "Credential used to authenticate with Home Assistant. The host "
                "must persist this value through a protected secret boundary."
            ),
            kind=SetupFieldKind.SECRET,
            required=True,
            environment_variable=TOKEN_ENV,
            legacy_environment_variable=LEGACY_TOKEN_ENV,
        ),
        SetupFieldDefinition(
            key="mapping_file",
            label="Mapping configuration",
            description=(
                "TOML file containing explicit logical targets and authorized "
                "Home Assistant actions."
            ),
            kind=SetupFieldKind.PATH,
            required=True,
            environment_variable=CONFIG_ENV,
            legacy_environment_variable=LEGACY_CONFIG_ENV,
        ),
        SetupFieldDefinition(
            key="timeout_seconds",
            label="Request timeout",
            description="Maximum provider request duration in seconds.",
            kind=SetupFieldKind.NUMBER,
            required=False,
            default=10.0,
        ),
    ),
)


def _environment_value(
    environ: Mapping[str, str],
    canonical: str | None,
    legacy: str | None,
) -> str:
    if canonical and environ.get(canonical, "").strip():
        return environ[canonical].strip()
    if legacy and environ.get(legacy, "").strip():
        return environ[legacy].strip()
    return ""


def evaluate_environment_setup(
    environ: Mapping[str, str],
) -> AvailabilityResult:
    missing = [
        field.key
        for field in HOME_ASSISTANT_SETUP.fields
        if field.required
        and not _environment_value(
            environ,
            field.environment_variable,
            field.legacy_environment_variable,
        )
    ]
    if missing:
        return AvailabilityResult(
            AvailabilityState.UNAVAILABLE,
            reason_code="home_assistant_setup_incomplete",
            diagnostic="Missing required Home Assistant setup fields: "
            + ", ".join(sorted(missing)),
        )

    try:
        HomeAssistantConnectionConfig.from_environment(environ=environ)
    except HomeAssistantConfigurationError as exc:
        return AvailabilityResult(
            AvailabilityState.UNAVAILABLE,
            reason_code="home_assistant_configuration_invalid",
            diagnostic=str(exc),
        )

    return AvailabilityResult.usable_result(
        "Required Home Assistant connection settings are configured."
    )


__all__ = [
    "HOME_ASSISTANT_SETUP",
    "SetupDefinition",
    "SetupFieldDefinition",
    "SetupFieldKind",
    "evaluate_environment_setup",
]
