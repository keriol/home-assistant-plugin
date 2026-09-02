from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import tomllib
from typing import Any

from butler_core import PluginDefinition

from wilfred_home_assistant.config import (
    HomeAssistantAction,
    HomeAssistantConfig,
    HomeAssistantTarget,
)
from wilfred_home_assistant.errors import HomeAssistantConfigurationError
from wilfred_home_assistant.plugin import create_plugin


CONFIG_ENV = "HAP_HOME_ASSISTANT_CONFIG"
LEGACY_CONFIG_ENV = "WILFRED_HOME_ASSISTANT_CONFIG"

_ALLOWED_TOP_LEVEL = frozenset({"actions", "targets"})
_ALLOWED_ACTION_KEYS = frozenset({"data", "domain", "service"})
_ALLOWED_TARGET_KEYS = frozenset({"device_id", "entity_id"})


def _require_table(document: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = document.get(key, {})
    if not isinstance(value, dict):
        raise HomeAssistantConfigurationError(
            f"Configuration section [{key}] must be a TOML table."
        )
    return value


def _load_mapping(
    path: Path,
) -> tuple[dict[str, str | HomeAssistantTarget], dict[str, HomeAssistantAction]]:
    if not path.is_file():
        raise HomeAssistantConfigurationError(
            f"Home Assistant configuration file does not exist: {path}"
        )

    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except tomllib.TOMLDecodeError as exc:
        raise HomeAssistantConfigurationError(
            f"Invalid Home Assistant TOML: {exc}"
        ) from exc
    except OSError as exc:
        raise HomeAssistantConfigurationError(
            f"Cannot read Home Assistant configuration file: {exc}"
        ) from exc

    unknown = sorted(set(document) - _ALLOWED_TOP_LEVEL)
    if unknown:
        raise HomeAssistantConfigurationError(
            "Unknown Home Assistant configuration sections: " + ", ".join(unknown)
        )

    raw_targets = _require_table(document, "targets")
    raw_actions = _require_table(document, "actions")

    targets: dict[str, str | HomeAssistantTarget] = {}
    for name, value in raw_targets.items():
        if isinstance(value, str):
            targets[name] = value
            continue

        if not isinstance(value, dict):
            raise HomeAssistantConfigurationError(
                f"Target {name!r} must map to a string entity_id or selector table."
            )

        unknown_target_keys = sorted(set(value) - _ALLOWED_TARGET_KEYS)
        if unknown_target_keys:
            raise HomeAssistantConfigurationError(
                f"Unknown keys for target {name!r}: " + ", ".join(unknown_target_keys)
            )

        entity_id = value.get("entity_id")
        device_id = value.get("device_id")
        if entity_id is not None and not isinstance(entity_id, str):
            raise HomeAssistantConfigurationError(
                f"Target {name!r}.entity_id must be a string."
            )
        if device_id is not None and not isinstance(device_id, str):
            raise HomeAssistantConfigurationError(
                f"Target {name!r}.device_id must be a string."
            )

        targets[name] = HomeAssistantTarget(entity_id=entity_id, device_id=device_id)

    actions: dict[str, HomeAssistantAction] = {}
    for name, value in raw_actions.items():
        if not isinstance(value, dict):
            raise HomeAssistantConfigurationError(
                f"Action {name!r} must be a TOML table."
            )
        unknown_action_keys = sorted(set(value) - _ALLOWED_ACTION_KEYS)
        if unknown_action_keys:
            raise HomeAssistantConfigurationError(
                f"Unknown keys for action {name!r}: "
                + ", ".join(unknown_action_keys)
            )
        domain = value.get("domain")
        service = value.get("service")
        data = value.get("data", {})
        if not isinstance(domain, str):
            raise HomeAssistantConfigurationError(
                f"Action {name!r}.domain must be a string."
            )
        if not isinstance(service, str):
            raise HomeAssistantConfigurationError(
                f"Action {name!r}.service must be a string."
            )
        if not isinstance(data, dict):
            raise HomeAssistantConfigurationError(
                f"Action {name!r}.data must be a TOML table."
            )
        actions[name] = HomeAssistantAction(
            domain=domain,
            service=service,
            data=data,
        )

    return targets, actions


def create_plugin_from_environment(
    environ: Mapping[str, str],
) -> PluginDefinition:
    config_path = (
        environ.get(CONFIG_ENV, "").strip()
        or environ.get(LEGACY_CONFIG_ENV, "").strip()
    )
    if not config_path:
        raise HomeAssistantConfigurationError(
            f"{CONFIG_ENV} is required."
        )

    targets, actions = _load_mapping(Path(config_path).expanduser())
    config = HomeAssistantConfig.from_environment(
        targets=targets,
        actions=actions,
        environ=environ,
    )
    return create_plugin(config)


__all__ = ["create_plugin_from_environment"]
