from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wilfred_home_assistant.client import HomeAssistantClient
from wilfred_home_assistant.config import HomeAssistantConfig
from wilfred_home_assistant.discovery import (
    DiscoveredHomeAssistantEntity,
    HomeAssistantDiscoveryClient,
)
from wilfred_home_assistant.errors import (
    HomeAssistantNotFoundError,
    HomeAssistantUnavailableError,
)


@dataclass(frozen=True)
class HomeAssistantResourceInspection:
    entity_id: str
    exists: bool
    metadata: dict[str, Any] | None
    state: dict[str, Any] | None
    provider_actions: tuple[str, ...]
    mapped_targets: tuple[str, ...]

    @property
    def authorized(self) -> bool:
        return bool(self.mapped_targets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "exists": self.exists,
            "metadata": self.metadata,
            "state": self.state,
            "provider_actions": list(self.provider_actions),
            "mapped_targets": list(self.mapped_targets),
            "authorized": self.authorized,
        }


@dataclass(frozen=True)
class HomeAssistantMappingValidation:
    target: str
    action: str | None
    entity_id: str | None
    provider_exists: bool
    provider_supports_action: bool | None
    mapped: bool
    authorized: bool
    valid: bool
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "action": self.action,
            "entity_id": self.entity_id,
            "provider_exists": self.provider_exists,
            "provider_supports_action": self.provider_supports_action,
            "mapped": self.mapped,
            "authorized": self.authorized,
            "valid": self.valid,
            "reason_code": self.reason_code,
        }


class HomeAssistantIntrospector:
    """READ-only provider facts and Butler mapping diagnostics."""

    def __init__(
        self,
        config: HomeAssistantConfig,
        client: HomeAssistantClient,
        discovery: HomeAssistantDiscoveryClient,
    ) -> None:
        self._config = config
        self._client = client
        self._discovery = discovery

    def _entities(self) -> dict[str, DiscoveredHomeAssistantEntity]:
        return {
            entity.entity_id: entity
            for entity in self._discovery.discover_entities()
        }

    def entity_exists(self, entity_id: str) -> bool:
        return entity_id in self._entities()

    def inspect_entity(self, entity_id: str) -> HomeAssistantResourceInspection:
        discovered = self._entities().get(entity_id)
        mapped_targets = tuple(
            sorted(
                name
                for name in self._config.targets
                if self._config.resolve_target_definition(name).entity_id == entity_id
            )
        )
        if discovered is None:
            return HomeAssistantResourceInspection(
                entity_id=entity_id,
                exists=False,
                metadata=None,
                state=None,
                provider_actions=(),
                mapped_targets=mapped_targets,
            )

        try:
            state = self._client.get_state(entity_id).to_dict()
        except (HomeAssistantNotFoundError, HomeAssistantUnavailableError):
            state = None

        return HomeAssistantResourceInspection(
            entity_id=entity_id,
            exists=True,
            metadata=discovered.to_dict(),
            state=state,
            provider_actions=self._discovery.services_for_entity(entity_id),
            mapped_targets=mapped_targets,
        )

    def validate_mapping(
        self,
        target: str,
        action: str | None = None,
    ) -> HomeAssistantMappingValidation:
        if target not in self._config.targets:
            return HomeAssistantMappingValidation(
                target=target,
                action=action,
                entity_id=None,
                provider_exists=False,
                provider_supports_action=None,
                mapped=False,
                authorized=False,
                valid=False,
                reason_code="target_not_mapped",
            )

        target_definition = self._config.resolve_target_definition(target)
        entity_id = target_definition.entity_id

        # READ semantics remain strictly entity-backed. A device selector
        # does not invent an observable Home Assistant state endpoint.
        if action is None:
            if entity_id is None:
                return HomeAssistantMappingValidation(
                    target=target,
                    action=None,
                    entity_id=None,
                    provider_exists=False,
                    provider_supports_action=None,
                    mapped=True,
                    authorized=False,
                    valid=False,
                    reason_code="target_not_entity_backed",
                )

            provider_exists = self.entity_exists(entity_id)
            if not provider_exists:
                return HomeAssistantMappingValidation(
                    target=target,
                    action=None,
                    entity_id=entity_id,
                    provider_exists=False,
                    provider_supports_action=None,
                    mapped=True,
                    authorized=False,
                    valid=False,
                    reason_code="provider_resource_missing",
                )

            return HomeAssistantMappingValidation(
                target=target,
                action=None,
                entity_id=entity_id,
                provider_exists=True,
                provider_supports_action=None,
                mapped=True,
                authorized=True,
                valid=True,
                reason_code="mapping_valid",
            )

        selector = target_definition.action_selector()

        if "device_id" in selector:
            device_id = selector["device_id"]
            provider_exists = any(
                entity.device_id == device_id
                for entity in self._entities().values()
            )
        else:
            provider_exists = self.entity_exists(selector["entity_id"])

        if not provider_exists:
            return HomeAssistantMappingValidation(
                target=target,
                action=action,
                entity_id=entity_id,
                provider_exists=False,
                provider_supports_action=None,
                mapped=True,
                authorized=False,
                valid=False,
                reason_code="provider_resource_missing",
            )

        action_definition = self._config.actions.get(action)
        if action_definition is None:
            return HomeAssistantMappingValidation(
                target=target,
                action=action,
                entity_id=entity_id,
                provider_exists=True,
                provider_supports_action=None,
                mapped=True,
                authorized=False,
                valid=False,
                reason_code="action_not_authorized",
            )

        provider_action = (
            f"{action_definition.domain}.{action_definition.service}"
        )
        provider_supports = provider_action in set(
            self._discovery.services_for_target(selector)
        )

        return HomeAssistantMappingValidation(
            target=target,
            action=action,
            entity_id=entity_id,
            provider_exists=True,
            provider_supports_action=provider_supports,
            mapped=True,
            authorized=provider_supports,
            valid=provider_supports,
            reason_code=(
                "mapping_valid"
                if provider_supports
                else "provider_action_not_applicable"
            ),
        )



__all__ = [
    "HomeAssistantIntrospector",
    "HomeAssistantMappingValidation",
    "HomeAssistantResourceInspection",
]
