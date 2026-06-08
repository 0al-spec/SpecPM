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

## Acceptance Policy

The current public index contains a generated `xyflow.core@0.1.0` candidate.
Package-set acceptance should treat that package as previous single-package
review evidence. It should not silently replace it.

A package-set accepted-source PR should decide explicitly whether
`xyflow.core` remains unchanged, is superseded by `xyflow.workspace` plus scoped
member packages, is kept as a compatibility package, or is removed in a later
review.

The expected package-set transition is:

- `xyflow.workspace` as the aggregate discovery entrypoint;
- `xyflow.system`, `xyflow.react`, and `xyflow.svelte` as scoped member package
  candidates;
- selected `contains` relations accepted only when both endpoints are selected.

Generated candidates may remain `preview_only` while they are producer drafts.
Removing `preview_only` requires explicit maintainer review of package subject,
evidence, claims, version, selected relations, and any `xyflow.core`
coexistence or supersession effect. Passing handoff preflight, AI enrichment
preflight, or `materialize-package-set` dry run is review evidence, not
acceptance.

## References

- `specs/XYFLOW_PACKAGE_SET_REFERENCE.md`
- `tests/fixtures/package_sets/xyflow-reference/`
- <doc:PackageSets>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:MultiPackageProducerIntake>
