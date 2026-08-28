from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from wilfred import CapabilityDefinition, DomainDefinition
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.plugins import PluginDefinition
from wilfred.registry import ToolRegistry

from wilfred_home_assistant import __version__
from wilfred_home_assistant.client import HomeAssistantClient
from wilfred_home_assistant.config import (
    HomeAssistantConfig,
    reject_target_override,
)


HOME_DOMAIN = DomainDefinition(
    name="home",
    description=(
        "Provider-neutral ownership of home state and control behavior."
    ),
)

HOME_STATE_CAPABILITY = CapabilityDefinition(
    name="state",
    domain=HOME_DOMAIN.identity,
    description=(
        "Read observable state through an authorized home integration."
    ),
)

HOME_CONTROL_CAPABILITY = CapabilityDefinition(
    name="control",
    domain=HOME_DOMAIN.identity,
    description=(
        "Request authorized home actions while preserving execution policy."
    ),
)


def create_plugin(
    config: HomeAssistantConfig,
    *,
    client: HomeAssistantClient | None = None,
) -> PluginDefinition:
    """Create a configured first-party Home Assistant plugin."""

    resolved_client = client or HomeAssistantClient(config)

    targets = sorted(config.targets)
    actions = sorted(config.actions)

    def register(registry: ToolRegistry) -> None:
        def get_state(target: str) -> dict[str, Any]:
            entity_id = config.resolve_target(target)

            return resolved_client.get_state(
                entity_id
            ).to_dict()

        registry.register(
            ToolDefinition(
                name="home_assistant_get_state",
                description=(
                    "Read the current Home Assistant state and "
                    "attributes of an authorized logical target."
                ),
                handler=get_state,
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "enum": targets,
                        },
                    },
                    "required": ["target"],
                    "additionalProperties": False,
                },
            )
        )

        def call_action(
            action: str,
            target: str,
            data: Mapping[str, Any] | None = None,
        ) -> dict[str, Any]:
            action_definition = config.resolve_action(action)
            entity_id = config.resolve_target(target)
            overrides = dict(data or {})

            reject_target_override(overrides)

            payload = dict(action_definition.data)
            payload.update(overrides)
            payload["entity_id"] = entity_id

            return resolved_client.call_service(
                action_definition.domain,
                action_definition.service,
                payload,
            )

        registry.register(
            ToolDefinition(
                name="home_assistant_call_action",
                description=(
                    "Dispatch a configured Home Assistant action "
                    "to an authorized logical target. Successful "
                    "dispatch does not prove physical state change."
                ),
                handler=call_action,
                permission=ToolPermission.ACTION,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": actions,
                        },
                        "target": {
                            "type": "string",
                            "enum": targets,
                        },
                        "data": {
                            "type": "object",
                        },
                    },
                    "required": [
                        "action",
                        "target",
                    ],
                    "additionalProperties": False,
                },
            )
        )

    return PluginDefinition(
        name="home-assistant",
        version=__version__,
        description=(
            "Official Home Assistant integration for Wilfred."
        ),
        register=register,
        domains=(HOME_DOMAIN,),
        capabilities=(
            HOME_CONTROL_CAPABILITY,
            HOME_STATE_CAPABILITY,
        ),
    )


__all__ = [
    "HOME_CONTROL_CAPABILITY",
    "HOME_DOMAIN",
    "HOME_STATE_CAPABILITY",
    "create_plugin",
]
