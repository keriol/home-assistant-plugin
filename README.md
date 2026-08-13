# Wilfred Home Assistant

Official first-party Home Assistant plugin for Wilfred.

```text
wilfred-home-assistant -> wilfred-butler -> butler-core
```

Home Assistant is optional. Wilfred remains usable without it, and Butler
Core remains provider-neutral.

## Status

`0.1.0.dev0` development.

The repository now provides the initial REST client, logical target and
authorized-action configuration, READ and ACTION tools, normalized errors and
READ -> ACTION -> READ -> VERIFY compatibility.

## Initial scope

- configurable Home Assistant URL and token;
- READ entity state and attributes;
- authorized ACTION service calls;
- normalized Home Assistant and transport errors;
- compatibility with Wilfred READ -> ACTION -> READ -> VERIFY;
- deterministic fake-transport tests;
- no household-specific entity IDs or credentials.

## Repository boundary

This repository owns Home Assistant-specific integration code.

`butler-wilfred` owns the runtime and acts as the official distribution hub.
It may compose tested plugin releases without vendoring their source.
