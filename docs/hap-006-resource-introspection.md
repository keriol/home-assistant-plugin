# HAP-006 — Resource introspection and mapping diagnostics

Home Assistant Plugin exposes READ-only provider introspection through normal Butler tools.

The intended call path is:

```text
semantic/domain plugin
        -> Butler runtime
        -> Core tool/capability contracts
        -> Home Assistant Plugin READ tool
        -> Home Assistant native APIs
        -> normalized result back through the same chain
```

Consumers do not need to import Home Assistant transport code directly.

## Provider-native sources

HAP uses Home Assistant as the source of truth:

- entity identity and registry metadata come from `config/entity_registry/list_for_display`;
- current state and attributes come from the Home Assistant REST state API;
- applicable provider actions come from `get_services_for_target` for the selected entity.

HAP does not persist a duplicate entity/device/area registry.

## Three distinct truths

HAP keeps the following concepts separate:

```text
provider resource exists
        !=
provider supports an action
        !=
Butler mapping authorizes that action
```

Discovery never grants execution permission.

A discovered entity may therefore exist and expose provider actions while remaining unavailable to the normal ACTION tool because no explicit logical target/action mapping authorizes it.

## READ-only tools

The plugin registers these diagnostic tools through the Core `ToolRegistry`:

- `home_assistant_entity_exists`
- `home_assistant_describe_entity`
- `home_assistant_list_entity_actions`
- `home_assistant_validate_mapping`

All use `ToolPermission.READ`.

The existing `home_assistant_call_action` remains the only ACTION surface and continues to accept configured logical targets/actions rather than arbitrary discovered entity/service identifiers.

## Mapping validation

`home_assistant_validate_mapping` reports structured reasons including:

- `target_not_mapped`
- `provider_resource_missing`
- `action_not_authorized`
- `provider_action_not_applicable`
- `mapping_valid`

This allows a generic runtime or setup flow to explain why a mapping cannot currently be used without duplicating Home Assistant semantics.

## Boundary

HAP owns provider-specific introspection and normalization.

The consuming runtime owns routing, policy, presentation and the decision to ask for this information. HAP declares no conversational utterances and does not promote Home Assistant identifiers into Butler Core contracts.
