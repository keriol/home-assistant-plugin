# Architecture

The plugin registers ordinary Wilfred tools.

READ operations use `ToolPermission.READ`.

State-changing operations use `ToolPermission.ACTION` or, when justified,
`ToolPermission.DANGEROUS`.

The plugin never grants confirmation.

A successful Home Assistant service dispatch proves only that dispatch
succeeded. Observable outcome verification remains owned by Wilfred's
READ-ACTION-VERIFY workflow.

Home Assistant REST semantics, authentication and error normalization live
here. Generic planning, permission policy and workflow orchestration do not.
