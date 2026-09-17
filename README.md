# Home Assistant Plugin

**Reusable Home Assistant integration for the Butler ecosystem.**

Repository: `keriol/home-assistant-plugin`  
Task namespace: **HAP**

Home Assistant Plugin (HAP) connects a Butler runtime to Home Assistant while
keeping the architectural boundary explicit:

```text
Butler runtime -> Home Assistant Plugin -> Home Assistant
```

Home Assistant continues to own devices, integrations, dashboards and physical
orchestration. The plugin owns reusable Home Assistant transport,
configuration, state reads, authorized actions and integration readiness
signals. The consuming Butler runtime owns composition, policy and semantic
routing.

## Why this repository exists

The plugin was originally created as the first real Home Assistant integration
and as a concrete proving example for Wilfred's public plugin/capability model.
That forced the model to work against a real external platform rather than only
a toy example.

HAP has since moved beyond being a Wilfred-specific integration. The current
`0.2.0.dev0` development line is a **consumer-neutral Butler plugin** built on
Butler Core contracts and usable independently by sibling Butler runtimes such
as Wilfred and Alfred:

```text
                Butler Core
                    |
          Home Assistant Plugin
             /              \
         Wilfred            Alfred
```

Wilfred and Alfred do not depend on each other in this model. They can consume
the same plugin because the reusable contract lives below them in Butler Core.

The consumer-neutral dependency migration was completed by **HAP-004**. The
Python distribution is now `butler-home-assistant` and the runtime dependency is
Butler Core rather than Wilfred. Historical `wilfred_home_assistant` naming is
retained only where compatibility or history requires it.

This is development state, not a claim that HAP `0.2.0` has been released.

## Why the boundary matters

Home Assistant is one smart-home platform, not a special case that Butler Core
must know about.

The broader architecture allows another home-automation manager to be
integrated by writing another plugin that follows the same Butler contracts:

```text
Butler runtime
    |
    +-> Home Assistant Plugin -> Home Assistant
    |
    +-> Another Home Plugin   -> another automation platform
```

That keeps Butler Core provider-neutral and prevents Wilfred or Alfred from
accumulating platform-specific device APIs in their runtime layers.

## Status

`0.2.0.dev0` development line.

The repository currently provides:

- a Home Assistant REST client with normalized transport/provider errors;
- logical target and authorized-action configuration;
- READ and ACTION tools based on Butler Core contracts;
- `home.state` and `home.control` capability declarations;
- READ-only plugin/capability readiness probes with structured failure reasons;
- Home Assistant readiness checks that do not mutate configuration or state;
- compatibility with `READ -> ACTION -> READ -> VERIFY` execution patterns;
- deterministic fake-transport tests;
- ratchets preventing runtime dependency on Wilfred;
- canonical `HAP_HOME_ASSISTANT_*` configuration names, with older Wilfred-prefixed names retained only as compatibility fallbacks where supported.

Direct adoption by a specific Butler runtime is tracked independently from the
plugin boundary itself. A consumer-neutral HAP does not make Wilfred or Alfred
depend on one another.

## Capability-first model

The plugin declares a provider-neutral `home` domain with two capabilities:

- `home.state`: read observable state through an authorized home integration;
- `home.control`: request authorized home actions while preserving execution
  policy.

Home Assistant is the integration that implements those capabilities. It does
not become the semantic owner of appliance, media, climate or other household
domains merely because those domains may use Home Assistant underneath.

## Reusable plugin contract

HAP uses Butler Core-owned contracts to describe itself to a consumer runtime,
including:

- stable plugin identity;
- human-readable metadata;
- tools and capabilities;
- readiness and per-capability availability where runtime prerequisites matter;
- structured reasons when a capability cannot currently be used.

Capabilities with no independent configuration or runtime prerequisite may be
statically/default available. Capabilities that depend on configuration,
authentication, connectivity or another prerequisite may expose observational
availability probes instead.

Availability checks are READ-only diagnostics. They do not repair
configuration, mutate credentials or perform actions against Home Assistant.

## Execution and ownership

READ operations use Butler Core `ToolPermission.READ`.

State-changing operations use `ToolPermission.ACTION` or, when justified,
`ToolPermission.DANGEROUS`.

The plugin never grants user confirmation and does not own runtime policy.
Successful Home Assistant dispatch is not proof of physical success. A
consuming runtime may compose post-action observation and verification through
Core-compatible execution patterns.

## Repository boundary

This repository owns reusable Home Assistant-specific integration code.

It does **not** own:

- Butler runtime discovery or lifecycle;
- Wilfred or Alfred composition;
- private household mappings;
- domain policy such as Laundry or media behavior;
- frontend-specific rendering;
- credentials or deployment-specific identifiers;
- Home Assistant physical orchestration itself.

Historical `WHA-*` and older `WILF-*` identifiers remain valid historical
aliases for work created before the repository/namespace cutover. New work uses
**HAP**.
