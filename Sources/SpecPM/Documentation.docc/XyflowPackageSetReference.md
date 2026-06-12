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
Package-set materialization treats that package as previous single-package
review evidence. It should not silently replace it.

The package-set accepted-source flow leaves `xyflow.core` unchanged as previous
single-package review evidence and accepts `xyflow.workspace`, `xyflow.react`,
`xyflow.svelte`, and `xyflow.system` through maintainer-curated artifacts under
`public-index/curated`.

The expected package-set transition is:

- `xyflow.workspace` as the aggregate discovery entrypoint;
- `xyflow.system`, `xyflow.react`, and `xyflow.svelte` as scoped member package
  entries;
- selected `contains` relation IDs are accepted in
  `public-index/accepted-packages.yml` only after both endpoints are accepted;
- generated SpecHarvester candidates, receipts, validation reports, and
  diagnostics remain producer evidence referenced from the curated artifacts.

Curated package-set entries do not keep `preview_only`, because the accepted
registry metadata is authored by maintainer review rather than copied as direct
producer output. This does not make the producer receipt an authority document:
passing handoff preflight, AI enrichment preflight, or `materialize-package-set`
dry run remains review evidence only. AI enrichment remains proposal-only and
does not alter accepted claims without explicit maintainer editing.

The broader lifecycle is documented in
<doc:CuratedAcceptedArtifactLifecycle>: generated candidates are immutable
evidence, curated artifacts own maintainer-authored accepted metadata, new
harvests update curated artifacts only through review diffs, evidence chains
are preserved through `foreignArtifacts`, `preview_only` removal is a
maintainer acceptance act, and relation acceptance remains separate from
package acceptance.

A later fresh `xyflow` run can be recorded as
`SpecPMGeneratedCandidateRefreshDecision` with `updateNeeded: false` and
`reason: no_contract_delta` when it reproduces the same contract-bearing
generated files and does not improve the curated accepted artifacts.
Producer receipt churn or a newly emitted quality report is review evidence,
not a reason to mutate `public-index/generated/xyflow.*` or churn accepted
registry metadata.

The example refresh decision fixture for this no-op outcome lives at
`tests/fixtures/refresh_decisions/xyflow-no-update.example.json`.

## References

- `specs/XYFLOW_PACKAGE_SET_REFERENCE.md`
- `tests/fixtures/package_sets/xyflow-reference/`
- <doc:GeneratedCandidateRefreshDecisionPolicy>
- <doc:PackageSets>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:MultiPackageProducerIntake>
- <doc:CuratedAcceptedArtifactLifecycle>
