# Home Assistant Plugin setup

Home Assistant Plugin owns the semantics required to configure its own provider connection. A Butler runtime or future generic control plane may render this setup without hard-coding Home Assistant-specific fields.

## Setup manifest

`HOME_ASSISTANT_SETUP` declares the current setup surface:

- `base_url`: required normal configuration;
- `token`: required secret configuration;
- `mapping_file`: required path to explicit logical target and authorized-action mappings;
- `timeout_seconds`: optional normal configuration with a default of 10 seconds.

The manifest exposes labels, descriptions, field kinds, required/optional state and environment compatibility metadata. It never contains a configured credential value.

The host owns persistence. In particular, a generic runtime/control plane should store the Home Assistant credential through a protected secret boundary and supply the resolved secret only to HAP at runtime.

## Environment compatibility

Canonical development environment variables are:

- `HAP_HOME_ASSISTANT_URL`;
- `HAP_HOME_ASSISTANT_TOKEN`;
- `HAP_HOME_ASSISTANT_CONFIG`.

The historical `WILFRED_HOME_ASSISTANT_*` names remain accepted as a compatibility path. They are not the canonical HAP identity.

`evaluate_environment_setup()` performs a safe preflight that reports missing or structurally invalid setup without exposing the credential value. Live authentication/connectivity remains an observational readiness check against Home Assistant.

## Configuration and authorization

Connection configuration and authorization mappings are intentionally distinct.

`HomeAssistantConnectionConfig` validates the provider URL, secret and transport timeout. `HomeAssistantConfig` extends that connection configuration with explicit logical target mappings and explicit authorized actions.

A discovered Home Assistant resource is therefore not executable merely because it exists:

```text
discovered resource != authorized Butler target
```

## Provider discovery

`HomeAssistantDiscoveryClient` uses Home Assistant's native WebSocket API and the read-only `config/entity_registry/list_for_display` command to obtain enabled entity-registry metadata.

HAP normalizes only the metadata useful for setup assistance:

- entity ID and domain;
- integration/platform;
- display name when available;
- native Home Assistant area ID reference;
- native Home Assistant device ID reference;
- labels.

HAP does not create a competing persistent entity/device/area registry. Device and area identifiers remain Home Assistant-owned references. Deeper resource description, current-state introspection, provider action applicability and mapping diagnostics are tracked separately by HAP-006.

Discovery never creates mappings or authorizes actions automatically.

## Authentication direction

The initial compatibility path supports manually supplied Home Assistant access tokens. The setup contract deliberately does not define persistence or acquisition as environment-only behavior, so a future browser/application authorization flow can replace manual token entry without changing Home Assistant semantics in consuming runtimes.
