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
configuration, state reads and authorized actions. The consuming Butler runtime
owns composition, policy and semantic routing.

## Why this repository exists

The plugin was originally created as the first real Home Assistant integration
and as a concrete proving example for Wilfred's public plugin/capability model.
That was useful because it forced the model to work against a real external
platform rather than only a toy example.

The project has now outgrown the idea of being a Wilfred-specific integration.
The intended direction is a **consumer-neutral Butler plugin** built on Butler
Core contracts and usable independently by sibling Butler runtimes such as
Wilfred and Alfred:

```text
                Butler Core
                    |
          Home Assistant Plugin
             /              \
         Wilfred            Alfred
```

Wilfred and Alfred do not depend on each other in this model. They can consume
the same plugin because the reusable contract lives below them in Butler Core.

This migration is tracked by **HAP-004**. Until that work is complete, some
runtime/package names and dependency details may still reflect the original
Wilfred-coupled implementation. The repository identity and architectural
direction described here are already canonical; implementation claims remain
grounded in merged/released evidence.

## Why the boundary matters

Home Assistant is one smart-home platform, not a special case that Butler Core
must know about.

The broader goal is that another home-automation manager can be integrated by
writing another plugin that follows the same Butler contracts:

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

`0.1.0.dev0` development line.

The repository currently provides the initial REST client, logical target and
authorized-action configuration, READ and ACTION tools, normalized errors,
capability-first semantic declarations and READ -> ACTION -> READ -> VERIFY
compatibility.

The consumer-neutral Core-only dependency migration, readiness/availability
contracts and direct Alfred adoption are active follow-up work, not completed
release claims.

## Capability-first model

The plugin currently declares a provider-neutral `home` domain with two
capabilities:

- `home.state`: read observable state through an authorized home integration;
- `home.control`: request authorized home actions while preserving execution
  policy.

Home Assistant is the integration that implements those capabilities. It does
not become the semantic owner of appliance, media, climate or other household
domains merely because those domains may use Home Assistant underneath.

## Initial scope

- configurable Home Assistant URL and token;
- READ entity state and attributes;
- authorized ACTION service calls;
- `home.state` and `home.control` capability declarations;
- normalized Home Assistant and transport errors;
- compatibility with READ -> ACTION -> READ -> VERIFY workflows;
- deterministic fake-transport tests;
- logical/configurable target mappings;
- no household-specific entity IDs, credentials or private policy.

## Planned reusable plugin contract

The next plugin boundary is designed to let a plugin describe itself to a
consumer runtime, including:

- stable plugin identity;
- human-readable name and description;
- tools and capabilities;
- semantic/frontend contributions where appropriate;
- readiness and per-capability availability through Butler Core contracts;
- structured reasons when a capability cannot currently be used.

Capabilities with no independent configuration or runtime prerequisite may be
statically/default available. Capabilities that depend on configuration,
authentication, connectivity or another prerequisite may expose observational
availability probes instead.

Availability checks are READ-only diagnostics. They do not repair
configuration, mutate credentials or perform actions against Home Assistant.

## Repository boundary

This repository owns reusable Home Assistant-specific integration code.

It does **not** own:

- Butler Core runtime discovery or lifecycle;
- Wilfred or Alfred composition;
- private household mappings;
- domain policy such as Laundry or media behavior;
- frontend-specific rendering;
- credentials or deployment-specific identifiers.

Historical `WHA-*` and older `WILF-*` identifiers remain valid historical
aliases for work created before the repository/namespace cutover. New work uses
**HAP**.
