from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from butler_core import (
    AvailabilityResult,
    AvailabilityState,
    CapabilityDefinition,
    DomainDefinition,
    PluginDefinition,
    ToolDefinition,
    ToolPermission,
    ToolRegistry,
)

from wilfred_home_assistant import __version__
from wilfred_home_assistant.client import HomeAssistantClient
from wilfred_home_assistant.config import HomeAssistantConfig, reject_target_override
from wilfred_home_assistant.discovery import HomeAssistantDiscoveryClient
from wilfred_home_assistant.errors import (
    HomeAssistantConnectionError,
    HomeAssistantResponseError,
    HomeAssistantUnauthorizedError,
)
from wilfred_home_assistant.introspection import HomeAssistantIntrospector


HOME_DOMAIN = DomainDefinition(
    name="home",
    description="Provider-neutral ownership of home state and control behavior.",
)

HOME_STATE_CAPABILITY = CapabilityDefinition(
    name="state",
    domain=HOME_DOMAIN.identity,
    description="Read observable state through an authorized home integration.",
)

HOME_CONTROL_CAPABILITY = CapabilityDefinition(
    name="control",
    domain=HOME_DOMAIN.identity,
    description="Request authorized home actions while preserving execution policy.",
)


def _readiness_probe(client: HomeAssistantClient) -> AvailabilityResult:
    try:
        client.check_api()
    except HomeAssistantUnauthorizedError:
        return AvailabilityResult(
            AvailabilityState.UNAVAILABLE,
            reason_code="home_assistant_authentication_failed",
            diagnostic="Home Assistant rejected the configured credential.",
        )
    except HomeAssistantConnectionError:
        return AvailabilityResult(
            AvailabilityState.UNAVAILABLE,
            reason_code="home_assistant_unreachable",
            diagnostic="Home Assistant endpoint is unreachable.",
        )
    except HomeAssistantResponseError:
        return AvailabilityResult(
            AvailabilityState.ERROR,
            reason_code="home_assistant_invalid_response",
            diagnostic="Home Assistant returned an invalid readiness response.",
        )

    return AvailabilityResult.usable_result("Home Assistant API is reachable.")


def create_plugin(
    config: HomeAssistantConfig,
    *,
    client: HomeAssistantClient | None = None,
    discovery: HomeAssistantDiscoveryClient | None = None,
) -> PluginDefinition:
    """Create a configured consumer-neutral Home Assistant plugin."""

    resolved_client = client or HomeAssistantClient(config)
    resolved_discovery = discovery or HomeAssistantDiscoveryClient(config)
    introspector = HomeAssistantIntrospector(
        config,
        resolved_client,
        resolved_discovery,
    )
    action_targets = sorted(config.targets)
    read_targets = sorted(
        name
        for name in config.targets
        if config.resolve_target_definition(name).entity_id is not None
    )
    actions = sorted(config.actions)

    def readiness() -> AvailabilityResult:
        return _readiness_probe(resolved_client)

    def register(registry: ToolRegistry) -> None:
        def get_state(target: str) -> dict[str, Any]:
            entity_id = config.resolve_target(target)
            return resolved_client.get_state(entity_id).to_dict()

        registry.register(
            ToolDefinition(
                name="home_assistant_get_state",
                description=(
                    "Read the current Home Assistant state and attributes of an "
                    "authorized logical target."
                ),
                handler=get_state,
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "enum": read_targets},
                    },
                    "required": ["target"],
                    "additionalProperties": False,
                },
            )
        )

        registry.register(
            ToolDefinition(
                name="home_assistant_entity_exists",
                description=(
                    "Check whether a Home Assistant entity exists in provider-native "
                    "discovery metadata. This does not authorize the entity."
                ),
                handler=lambda entity_id: {
                    "entity_id": entity_id,
                    "exists": introspector.entity_exists(entity_id),
                },
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {"entity_id": {"type": "string"}},
                    "required": ["entity_id"],
                    "additionalProperties": False,
                },
            )
        )

        registry.register(
            ToolDefinition(
                name="home_assistant_describe_entity",
                description=(
                    "Describe a Home Assistant entity using provider metadata, current "
                    "state and applicable provider actions without authorizing it."
                ),
                handler=lambda entity_id: introspector.inspect_entity(
                    entity_id
                ).to_dict(),
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {"entity_id": {"type": "string"}},
                    "required": ["entity_id"],
                    "additionalProperties": False,
                },
            )
        )

        registry.register(
            ToolDefinition(
                name="home_assistant_list_entity_actions",
                description=(
                    "List Home Assistant provider actions applicable to an entity. "
                    "Provider applicability does not imply Butler authorization."
                ),
                handler=lambda entity_id: {
                    "entity_id": entity_id,
                    "provider_actions": list(
                        resolved_discovery.services_for_entity(entity_id)
                    ),
                },
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {"entity_id": {"type": "string"}},
                    "required": ["entity_id"],
                    "additionalProperties": False,
                },
            )
        )

        registry.register(
            ToolDefinition(
                name="home_assistant_validate_mapping",
                description=(
                    "Validate a configured logical target and optional authorized action "
                    "against current Home Assistant provider facts."
                ),
                handler=lambda target, action=None: introspector.validate_mapping(
                    target,
                    action,
                ).to_dict(),
                permission=ToolPermission.READ,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "action": {"type": "string"},
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
            target_selector = config.resolve_action_target(target)
            overrides = dict(data or {})
            reject_target_override(overrides)
            payload = dict(action_definition.data)
            payload.update(overrides)
            payload.update(target_selector)
            return resolved_client.call_service(
                action_definition.domain,
                action_definition.service,
                payload,
            )

        registry.register(
            ToolDefinition(
                name="home_assistant_call_action",
                description=(
                    "Dispatch a configured Home Assistant action to an authorized "
                    "logical target. Successful dispatch does not prove physical "
                    "state change."
                ),
                handler=call_action,
                permission=ToolPermission.ACTION,
                category="home-assistant",
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": actions},
                        "target": {"type": "string", "enum": action_targets},
                        "data": {"type": "object"},
                    },
                    "required": ["action", "target"],
                    "additionalProperties": False,
                },
            )
        )

    capabilities = (
        CapabilityDefinition(
            name=HOME_CONTROL_CAPABILITY.name,
            domain=HOME_CONTROL_CAPABILITY.domain,
            description=HOME_CONTROL_CAPABILITY.description,
            availability_probe=readiness,
        ),
        CapabilityDefinition(
            name=HOME_STATE_CAPABILITY.name,
            domain=HOME_STATE_CAPABILITY.domain,
            description=HOME_STATE_CAPABILITY.description,
            availability_probe=readiness,
        ),
    )

    return PluginDefinition(
        name="home-assistant",
        version=__version__,
        description="Reusable Home Assistant integration for Butler runtimes.",
        register=register,
        domains=(HOME_DOMAIN,),
        capabilities=capabilities,
        readiness_probe=readiness,
    )


__all__ = [
    "HOME_CONTROL_CAPABILITY",
    "HOME_DOMAIN",
    "HOME_STATE_CAPABILITY",
    "create_plugin",
]
