"""Official Home Assistant plugin for Wilfred."""

from importlib.metadata import PackageNotFoundError, version as package_version

try:
    __version__ = package_version("wilfred-home-assistant")
except PackageNotFoundError:
    __version__ = "0+unknown"

from wilfred_home_assistant.client import (
    HomeAssistantClient,
    HomeAssistantState,
)
from wilfred_home_assistant.config import (
    HomeAssistantAction,
    HomeAssistantConfig,
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
from wilfred_home_assistant.plugin import create_plugin

__all__ = [
    "HomeAssistantAction",
    "HomeAssistantClient",
    "HomeAssistantConfig",
    "HomeAssistantConfigurationError",
    "HomeAssistantConnectionError",
    "HomeAssistantError",
    "HomeAssistantNotFoundError",
    "HomeAssistantResponseError",
    "HomeAssistantState",
    "HomeAssistantUnauthorizedError",
    "HomeAssistantUnavailableError",
    "create_plugin",
    "__version__",
]
