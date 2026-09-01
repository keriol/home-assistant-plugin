# HAP-004 consumer-neutral migration

Home Assistant Plugin is moving from its historical Wilfred-coupled development shape to an independent Butler plugin.

## Canonical identity

- Repository/project: **Home Assistant Plugin (HAP)**
- Development distribution: `butler-home-assistant`
- Development version: `0.2.0.dev0`
- Contract dependency: Butler Core development line containing CORE-014

The historical Python import namespace `wilfred_home_assistant` is retained temporarily as a compatibility surface. Keeping that import path does not imply a Wilfred runtime dependency. A later namespace removal/alias decision can be made with explicit consumer evidence rather than forcing an unrelated breaking import migration into HAP-004.

## Dependency boundary

Runtime source imports provider-neutral contracts directly from `butler_core`. The distribution no longer depends on `wilfred-butler` and must not acquire an Alfred dependency.

During development HAP pins the exact Butler Core development commit it is proving against. Before HAP 0.2.0 is released, HAP-007 requires replacing that development pin with the immutable released Core artifact containing the proven contract set.

## Configuration compatibility

Canonical environment variables are:

- `HAP_HOME_ASSISTANT_URL`
- `HAP_HOME_ASSISTANT_TOKEN`
- `HAP_HOME_ASSISTANT_CONFIG`

Historical `WILFRED_HOME_ASSISTANT_*` names remain accepted as compatibility fallbacks during the migration. New integrations and documentation should use the HAP-prefixed names.

## Readiness

The plugin uses CORE-014 observational readiness contracts. The readiness probe performs a READ-only Home Assistant API check and returns structured results for usable, authentication failure, unreachable endpoint and invalid provider response cases.

Readiness checks never repair configuration, change credentials or perform Home Assistant actions.

## Ownership

HAP owns Home Assistant transport, configuration, authorized logical mappings, typed tools and provider readiness. Consuming runtimes own loading, routing, policy, help and diagnostics presentation. Home Assistant remains the source of truth for devices and physical orchestration.
