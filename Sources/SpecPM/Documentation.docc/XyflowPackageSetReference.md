# Xyflow Package Set Reference

Reference scenario for package sets in a real monorepo.

## Overview

The `xyflow` repository shows why package sets are useful. One broad package can
overclaim the repository, while one scoped package can lose product-level
discovery intent.

The reference package family is:

```text
xyflow.workspace  aggregate discovery entrypoint
xyflow.system     scoped system package
xyflow.react      scoped React package
xyflow.svelte     scoped Svelte package
```

## Source Snapshot

The scenario uses the local `xyflow` source snapshot:

```text
revision: a58568f11bc0e1a1bdca1b3549e959e2e1ca0cdd
workspace: pnpm-workspace.yaml -> packages/*, examples/*, tooling/*, tests/*
```

Observed packages:

- `packages/system`: `@xyflow/system`
- `packages/react`: `@xyflow/react`
- `packages/svelte`: `@xyflow/svelte`

## Search Expectations

Exact lookup for `intent.ui.node_based_editor` may return:

```text
xyflow.workspace scope=aggregate match=direct
xyflow.react     scope=package   match=direct
xyflow.svelte    scope=package   match=direct
```

Exact lookup for `intent.ui.flow_system_utilities` may return:

```text
xyflow.system scope=package match=direct
```

## Fixtures

Non-normative example payloads live under:

```text
tests/fixtures/package_sets/xyflow-reference/
```

They show workspace inventory, package-set metadata, relation proposals, and
intent search result scope examples. They are not current public `/v0` payloads.

## References

- `specs/XYFLOW_PACKAGE_SET_REFERENCE.md`
- `tests/fixtures/package_sets/xyflow-reference/`
- <doc:PackageSets>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:MultiPackageProducerIntake>
