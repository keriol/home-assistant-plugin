# Architecture

Home Assistant Plugin (HAP) is the reusable Home Assistant integration boundary
for Butler runtimes.

The dependency shape is:

```text
                Butler Core
                    |
          Home Assistant Plugin
             /              \
         Wilfred            Alfred
```

HAP depends on Butler Core contracts rather than on a concrete Butler runtime.
Wilfred and Alfred are sibling consumers and do not depend on each other in
order to use the same Home Assistant integration package.

Home Assistant remains the owner of devices, integrations, dashboards and
physical orchestration. HAP owns reusable Home Assistant transport,
authentication, configuration, state reads, authorized actions and
provider-readiness diagnostics. The consuming runtime owns composition, policy,
semantic routing and higher-level workflow behavior.

## Capability-first ownership

The plugin declares the provider-neutral `home` domain and two capabilities:

- `home.state` for reading observable state through an authorized home
  integration;
- `home.control` for requesting authorized home actions while preserving
  runtime execution policy.

Home Assistant is the integration/provider that implements those capabilities.
It is not the semantic owner of appliance, media, climate or other household
domains merely because those domains may use Home Assistant underneath.

Capability and tool declarations use Butler Core-owned contracts. The plugin
does not create a runtime-specific executable registry or make Wilfred-specific
conversation behavior part of the integration boundary.

The plugin should declare deterministic resolvers only when reusable
request-resolution behavior genuinely belongs to the capability. Provider- or
household-specific keyword tables do not belong in HAP.

## Execution boundary

READ operations use Butler Core `ToolPermission.READ`.

State-changing operations use `ToolPermission.ACTION` or, when justified,
`ToolPermission.DANGEROUS`.

HAP never grants user confirmation and does not own consumer runtime policy.

A successful Home Assistant service dispatch proves only that dispatch
succeeded. Where the requested physical outcome can be observed, the consuming
runtime may compose the preferred lifecycle:

```text
READ -> ACTION -> READ -> VERIFY
```

HAP provides the reusable reads/actions and provider diagnostics needed by such
workflows, but generic planning, confirmation, orchestration and semantic
composition remain runtime responsibilities.

## Readiness and availability

HAP can expose READ-only readiness and capability-availability probes through
Butler Core contracts.

These probes may observe prerequisites such as configuration, authentication,
connectivity or provider response validity and return structured reasons when a
capability is unavailable.

Readiness checks are diagnostics only. They must not repair configuration,
mutate credentials, perform Home Assistant actions or silently change runtime
policy.

## Dependency and compatibility boundary

The `0.2.0.dev0` development line uses Butler Core as its runtime contract
dependency. HAP-004 removed the architectural runtime dependency on Wilfred.

Historical `wilfred_home_assistant` import/configuration names may remain as
explicit compatibility surfaces during migration. Compatibility naming must not
be interpreted as architectural ownership by Wilfred.

This is development state and does not imply that HAP `0.2.0` has been
released.

## Public boundary

Configuration exposes logical targets and authorized actions rather than
household policy.

The package must not contain:

- private deployment URLs or credentials;
- household-specific entity identifiers in reusable defaults;
- private orchestration policy;
- Alfred-specific behavior;
- frontend-specific rendering concerns.

Reusable Home Assistant integration code belongs here. Physical orchestration
remains in Home Assistant; Butler runtime composition remains in the consuming
runtime.
