# Configuration

The Home Assistant plugin requires a server URL and an access token.

Credentials can be supplied through:

- `WILFRED_HOME_ASSISTANT_URL`
- `WILFRED_HOME_ASSISTANT_TOKEN`

Credentials must never be committed to the repository or exposed through tool
schemas.

## Logical targets

The plugin does not hardcode household entity IDs.

Applications supply a mapping from public logical names to Home Assistant
entity IDs.

Example:

    desk_light -> light.demo_desk

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

For example:

    turn_on -> light.turn_on

The ACTION tool remains subject to Wilfred's normal confirmation policy.

Caller-supplied action data cannot override `entity_id`, `device_id`,
`area_id` or `target`. This prevents a configured action from escaping the
authorized logical target.

## Verification

A successful service response proves dispatch only.

Use Wilfred's existing READ-ACTION-VERIFY workflow to read observable state
again after dispatch and determine whether the requested outcome actually
occurred.

## Standalone bootstrap

A standalone Wilfred distribution can construct this plugin dynamically from
environment variables and a TOML mapping file.

Factory specification:

    wilfred_home_assistant.bootstrap:create_plugin_from_environment

Required environment variables:

    WILFRED_HOME_ASSISTANT_URL
    WILFRED_HOME_ASSISTANT_TOKEN
    WILFRED_HOME_ASSISTANT_CONFIG

The configuration file contains only target mappings and explicitly authorized
actions.

Example:

    [targets]
    demo_light = "light.demo"

    [actions.turn_on]
    domain = "light"
    service = "turn_on"

The access token does not belong in this TOML file.

The file is application configuration and must not be committed when it
contains household-specific entity identifiers.
