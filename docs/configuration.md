# Configuration

The Home Assistant plugin requires a server URL and an access token.

Canonical credentials are supplied through:

- `HAP_HOME_ASSISTANT_URL`
- `HAP_HOME_ASSISTANT_TOKEN`

Historical `WILFRED_HOME_ASSISTANT_*` names remain compatibility fallbacks where documented.
Credentials must never be committed to the repository or exposed through tool schemas.

## Logical targets

The plugin does not hardcode household entity IDs.

Applications supply mappings from logical names to Home Assistant targets.
The historical entity-only TOML form remains supported:

    [targets]
    desk_light = "light.demo_desk"

ACTION targets can instead use an explicit Home Assistant selector:

    [targets]
    tv_remote = { device_id = "device-demo-tv" }

A logical target may declare both an observable entity and an ACTION device:

    [targets]
    tv_remote = { entity_id = "remote.demo_tv", device_id = "device-demo-tv" }

When both are present, READ/VERIFY uses `entity_id` while ACTION dispatch uses
`device_id`. A device-only target is ACTION-only and is not exposed as a
readable state target. Provider identifiers remain integration configuration
and discovery never authorizes arbitrary targets.

## Authorized actions

Arbitrary Home Assistant service calls are not exposed as planner tools.
Applications explicitly configure allowed logical actions, each mapped to a
Home Assistant domain and service.

Targeted actions are the default and remain backward compatible:

    [targets]
    desk_light = "light.demo_desk"

    [actions.turn_on]
    domain = "light"
    service = "turn_on"

A targeted action requires an authorized logical target when invoked.

Some Home Assistant services are legitimately parameterized without an entity,
device or area selector. These may be authorized explicitly as targetless:

    [actions.run_scene_script]
    domain = "script"
    service = "run_scene_script"
    target_required = false

`target_required` defaults to `true`. A targetless action is still authorized by
its logical action name and still uses the normal Butler ACTION confirmation
policy. It does not provide arbitrary service passthrough. Supplying a target to
an explicitly targetless action is rejected rather than silently ignored.

Caller-supplied action data cannot override `entity_id`, `device_id`, `area_id`
or `target` in either mode. This prevents action data from escaping configured
authorization boundaries.

## Verification

A successful service response proves dispatch only.

The consuming Butler runtime or semantic owner should perform an observable
post-action READ/VERIFY when physical outcome verification is required.

## Standalone bootstrap

A Butler runtime can construct this plugin dynamically from environment
variables and a TOML mapping file.

Factory specification:

    wilfred_home_assistant.bootstrap:create_plugin_from_environment

Canonical environment variables:

    HAP_HOME_ASSISTANT_URL
    HAP_HOME_ASSISTANT_TOKEN
    HAP_HOME_ASSISTANT_CONFIG

The configuration file contains only logical target mappings and explicitly
authorized actions. The access token does not belong in this TOML file.

The file is application configuration and must not be committed when it
contains household-specific identifiers.
