from __future__ import annotations


class HomeAssistantError(RuntimeError):
    """Base error exposed by the Home Assistant integration."""

    code = "home_assistant_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class HomeAssistantConfigurationError(HomeAssistantError):
    code = "configuration_error"


class HomeAssistantUnauthorizedError(HomeAssistantError):
    code = "unauthorized"


class HomeAssistantNotFoundError(HomeAssistantError):
    code = "not_found"


class HomeAssistantUnavailableError(HomeAssistantError):
    code = "unavailable"


class HomeAssistantConnectionError(HomeAssistantError):
    code = "connection_error"


class HomeAssistantResponseError(HomeAssistantError):
    code = "response_error"
