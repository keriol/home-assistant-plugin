from butler_core import AvailabilityState

from wilfred_home_assistant.setup import (
    HOME_ASSISTANT_SETUP,
    SetupFieldKind,
    evaluate_environment_setup,
)


def test_setup_manifest_is_consumer_neutral_and_secret_safe() -> None:
    payload = HOME_ASSISTANT_SETUP.to_safe_dict()

    assert payload["plugin"] == "home-assistant"
    assert [field["key"] for field in payload["fields"]] == [
        "base_url",
        "token",
        "mapping_file",
        "timeout_seconds",
    ]

    token = next(
        field
        for field in HOME_ASSISTANT_SETUP.fields
        if field.key == "token"
    )
    assert token.kind is SetupFieldKind.SECRET
    assert token.required is True
    assert token.secret is True
    assert "secret-value" not in repr(payload)


def test_setup_preflight_reports_missing_fields_without_secret_values() -> None:
    result = evaluate_environment_setup(
        {
            "HAP_HOME_ASSISTANT_URL": "https://ha.example",
        }
    )

    assert result.state is AvailabilityState.UNAVAILABLE
    assert result.reason_code == "home_assistant_setup_incomplete"
    assert "token" in (result.diagnostic or "")
    assert "mapping_file" in (result.diagnostic or "")


def test_setup_preflight_accepts_canonical_environment() -> None:
    result = evaluate_environment_setup(
        {
            "HAP_HOME_ASSISTANT_URL": "https://ha.example",
            "HAP_HOME_ASSISTANT_TOKEN": "secret-value",
            "HAP_HOME_ASSISTANT_CONFIG": "/config/home-assistant.toml",
        }
    )

    assert result.state is AvailabilityState.USABLE
    assert "secret-value" not in (result.diagnostic or "")


def test_setup_preflight_keeps_legacy_environment_compatible() -> None:
    result = evaluate_environment_setup(
        {
            "WILFRED_HOME_ASSISTANT_URL": "https://ha.example",
            "WILFRED_HOME_ASSISTANT_TOKEN": "legacy-secret",
            "WILFRED_HOME_ASSISTANT_CONFIG": "/config/home-assistant.toml",
        }
    )

    assert result.state is AvailabilityState.USABLE
    assert "legacy-secret" not in (result.diagnostic or "")


def test_setup_preflight_rejects_invalid_connection_config() -> None:
    result = evaluate_environment_setup(
        {
            "HAP_HOME_ASSISTANT_URL": "not-a-url",
            "HAP_HOME_ASSISTANT_TOKEN": "secret-value",
            "HAP_HOME_ASSISTANT_CONFIG": "/config/home-assistant.toml",
        }
    )

    assert result.state is AvailabilityState.UNAVAILABLE
    assert result.reason_code == "home_assistant_configuration_invalid"
    assert "secret-value" not in (result.diagnostic or "")
