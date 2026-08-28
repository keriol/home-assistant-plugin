# Architecture

The plugin is the Home Assistant integration boundary for Wilfred. Home Assistant remains the owner of devices, integrations and physical orchestration; this package exposes reusable provider-neutral behavior without embedding household policy.

## Capability-first ownership

The plugin declares the Wilfred domain `home` and two public capabilities:

- `home.state` for reading observable state through an authorized home integration;
- `home.control` for requesting authorized home actions while preserving Wilfred execution policy.

Home Assistant is the integration/provider that implements those capabilities. It is not the domain itself.

The capability declarations are semantic metadata. Executable operations remain ordinary Wilfred tools in the existing `ToolRegistry`; the plugin does not create a second executable registry.

The current plugin does not declare deterministic resolvers. Resolver ownership belongs to a capability only when reusable deterministic request-resolution behavior actually exists. Provider-specific or household-specific keyword tables do not belong here.

## Execution boundary

READ operations use `ToolPermission.READ`.

State-changing operations use `ToolPermission.ACTION` or, when justified,
`ToolPermission.DANGEROUS`.

The plugin never grants confirmation.

A successful Home Assistant service dispatch proves only that dispatch succeeded. Observable outcome verification remains owned by Wilfred's `READ -> ACTION -> READ -> VERIFY` workflow. Capability ownership does not bypass that workflow, `ExecutionEngine`, confirmation or policy.

Home Assistant REST semantics, authentication and error normalization live here. Generic planning, permission policy, capability composition and workflow orchestration remain Wilfred responsibilities.

## Public boundary

Configuration exposes logical targets and authorized actions only. The package must not contain private deployment URLs, household entity IDs, credentials or private orchestration policy.
