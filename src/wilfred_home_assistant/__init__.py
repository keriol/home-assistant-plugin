"""Reusable Home Assistant plugin for Butler runtimes.

The historical ``wilfred_home_assistant`` import namespace is retained as a
compatibility surface while package ownership moves to Home Assistant Plugin.
"""

from importlib.metadata import PackageNotFoundError, version as package_version

try:
    __version__ = package_version("butler-home-assistant")
except PackageNotFoundError:
    __version__ = "0+unknown"

from wilfred_home_assistant.client import (
    HomeAssistantClient,
    HomeAssistantState,
)
from wilfred_home_assistant.config import (
    HomeAssistantAction,
    HomeAssistantConfig,
    HomeAssistantConnectionConfig,
    HomeAssistantTarget,
)
from wilfred_home_assistant.discovery import (
    DiscoveredHomeAssistantEntity,
    HomeAssistantDiscoveryClient,
)
from wilfred_home_assistant.errors import (
    HomeAssistantConfigurationError,
    HomeAssistantConnectionError,
    HomeAssistantError,
    HomeAssistantNotFoundError,
    HomeAssistantResponseError,
    HomeAssistantUnauthorizedError,
    HomeAssistantUnavailableError,
)
from wilfred_home_assistant.introspection import (
    HomeAssistantIntrospector,
    HomeAssistantMappingValidation,
    HomeAssistantResourceInspection,
)
from wilfred_home_assistant.plugin import create_plugin
from wilfred_home_assistant.setup import (
    HOME_ASSISTANT_SETUP,
    SetupDefinition,
    SetupFieldDefinition,
    SetupFieldKind,
    evaluate_environment_setup,
)

__all__ = [
    "DiscoveredHomeAssistantEntity",
    "HOME_ASSISTANT_SETUP",
    "HomeAssistantAction",
    "HomeAssistantClient",
    "HomeAssistantConfig",
    "HomeAssistantConfigurationError",
    "HomeAssistantConnectionConfig",
    "HomeAssistantConnectionError",
    "HomeAssistantDiscoveryClient",
    "HomeAssistantTarget",
    "HomeAssistantError",
    "HomeAssistantIntrospector",
    "HomeAssistantMappingValidation",
    "HomeAssistantNotFoundError",
    "HomeAssistantResourceInspection",
    "HomeAssistantResponseError",
    "HomeAssistantState",
    "HomeAssistantUnauthorizedError",
    "HomeAssistantUnavailableError",
    "SetupDefinition",
    "SetupFieldDefinition",
    "SetupFieldKind",
    "create_plugin",
    "evaluate_environment_setup",
    "__version__",
]
