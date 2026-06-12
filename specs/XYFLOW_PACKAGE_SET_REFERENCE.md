# Xyflow Package Set Reference Scenario

Status: Accepted reference scenario
Updated: 2026-06-09
Scope: reference scenario for package sets, monorepo discovery, and scoped
package candidates

## Purpose

This reference scenario shows how a multi-package repository can preserve broad
product discovery intent without overclaiming one scoped package.

It is a reference for the accepted public index package-set shape. It does not
make SpecHarvester output registry authority: generated candidates remain
producer evidence, and maintainer-curated artifacts are the accepted sources.

## Source Context

Local source snapshot inspected for this scenario:

```text
repository: https://github.com/xyflow/xyflow
revision: a58568f11bc0e1a1bdca1b3549e959e2e1ca0cdd
workspace: pnpm-workspace.yaml -> packages/*, examples/*, tooling/*, tests/*
```

Observed package manifests:

| Path | Package | Description role |
| --- | --- | --- |
| `package.json` | `@xyflow/monorepo` | Repository-level product description. |
| `packages/system/package.json` | `@xyflow/system` | Shared system package powering React Flow and Svelte Flow. |
| `packages/react/package.json` | `@xyflow/react` | React package for node-based editors and interactive flow charts. |
| `packages/svelte/package.json` | `@xyflow/svelte` | Svelte package for node-based editors, workflow systems, diagrams, and more. |

## Problem Shown by Previous Candidates

A single `xyflow.core` candidate can fail in two opposite ways:

- if it represents the whole repository, it can overclaim package-level
  capabilities that belong to `packages/react`, `packages/svelte`, or
  `packages/system`;
- if it represents only `packages/system`, it can lose the broader public
  product intent that makes `xyflow` discoverable for node-based editors and
  interactive flow charts.

The package-set model keeps both views:

```text
xyflow.workspace  aggregate discovery entrypoint
xyflow.system     scoped system package
xyflow.react      scoped React package
xyflow.svelte     scoped Svelte package
```

## Accepted Package Subjects

### `xyflow.workspace`

Role:

- aggregate package set.

Evidence:

- root `package.json`;
- `pnpm-workspace.yaml`;
- package manifest list.

Intent:

```text
xyflow workspace for node-based editors and interactive flow systems.
```

Expected search scope:

```text
scope=aggregate
```

### `xyflow.system`

Role:

- scoped system package for shared flow utilities.

Evidence:

- `packages/system/package.json`;
- `packages/system` source and public interface evidence.

Intent:

```text
shared system layer powering React Flow and Svelte Flow.
```

Expected search scope:

```text
scope=package
```

### `xyflow.react`

Role:

- scoped React package.

Evidence:

- `packages/react/package.json`;
- `packages/react` source and public interface evidence.

Intent:

```text
React package for building node-based editors and interactive flow charts.
```

Expected search scope:

```text
scope=package
```

### `xyflow.svelte`

Role:

- scoped Svelte package.

Evidence:

- `packages/svelte/package.json`;
- `packages/svelte` source and public interface evidence.

Intent:

```text
Svelte package for building node-based editors, workflow systems, diagrams, and related interfaces.
```

Expected search scope:

```text
scope=package
```

## Accepted Relations

```text
xyflow.workspace contains xyflow.system
xyflow.workspace contains xyflow.react
xyflow.workspace contains xyflow.svelte
```

Evidence:

- `pnpm-workspace.yaml`;
- package manifest paths;
- maintainer review of the proposed package-set membership.

The `contains` relation does not make members inherit aggregate capabilities,
trust, lifecycle state, namespace ownership, or acceptance status.

## Maintainer-Curated Accepted Artifacts

The public index accepts the package-set members from:

```text
public-index/curated/xyflow.workspace/0.1.0
public-index/curated/xyflow.react/0.1.0
public-index/curated/xyflow.svelte/0.1.0
public-index/curated/xyflow.system/0.1.0
```

The corresponding SpecHarvester outputs remain in:

```text
public-index/generated/xyflow.workspace/0.1.0
public-index/generated/xyflow.react/0.1.0
public-index/generated/xyflow.svelte/0.1.0
public-index/generated/xyflow.system/0.1.0
```

Curated manifests reference generated `specpm.yaml`, `producer-receipt.json`,
and validation reports as `foreignArtifacts` using repository URIs. They do not
edit generated files, update producer receipt hashes, or pretend that
maintainer-authored text was emitted by SpecHarvester.

The curated entries omit `preview_only` because they are accepted registry
metadata after maintainer review. This acceptance is scoped to the curated
claims and accepted `contains` relations; it does not grant upstream
endorsement, dependency-solving semantics, trust propagation, or automatic
acceptance of future producer output.

## Search Expectations

Exact lookup for:

```text
intent.ui.node_based_editor
```

may return:

```text
xyflow.workspace scope=aggregate match=direct
xyflow.react     scope=package   match=direct
xyflow.svelte    scope=package   match=direct
```

Exact lookup for:

```text
intent.ui.flow_system_utilities
```

may return:

```text
xyflow.system scope=package match=direct
```

The workspace result should not appear for the narrower system-utilities intent
unless the package set explicitly declares that aggregate intent.

## Fixture Files

Non-normative example payloads are stored under:

```text
tests/fixtures/package_sets/xyflow-reference/
```

They show:

- workspace inventory;
- package-set metadata;
- relation proposal metadata;
- exact intent search result scope.

These fixtures are examples for review and future implementation. They are not
current public `/v0` payloads.

## Acceptance Boundary

The current public index already contains a generated `xyflow.core@0.1.0`
candidate. The package-set materialization treats that package as previous
single-package review evidence, not as an automatic conflict and not as the
canonical long-term model by itself.

For the package-set transition, maintainers reviewed the replacement shape
explicitly:

- `xyflow.workspace` is the aggregate discovery entrypoint for the repository;
- `xyflow.system`, `xyflow.react`, and `xyflow.svelte` are scoped member
  package candidates;
- `xyflow.workspace contains <member>` relation IDs are selected as
  maintainer-review evidence only when both endpoints are selected;
- `xyflow.core` is left unchanged as previous single-package review evidence.

The accepted-source materialization now accepts maintainer-curated artifacts:

- `public-index/curated/xyflow.workspace/0.1.0`;
- `public-index/curated/xyflow.react/0.1.0`;
- `public-index/curated/xyflow.svelte/0.1.0`;
- `public-index/curated/xyflow.system/0.1.0`.

These curated artifacts are the registry source and own the
maintainer-authored accepted metadata. The corresponding generated candidates
under `public-index/generated/xyflow.*` remain immutable producer evidence.

The generated package-set manifests may keep `preview_only: true` while they
remain producer drafts. The curated package-set entries omit `preview_only`
because maintainers reviewed the package subjects, evidence, claims, versions,
selected relations, and `xyflow.core` coexistence.

Stable `/v0` relation metadata is published only from explicit
`public-index/accepted-packages.yml` `relations[]` entries. Producer relation
proposals remain evidence until selected by maintainers.

Accepting the package set does not accept all members. Accepting a member does
not accept the package set. Accepting a relation does not grant trust or
selection authority.

Generated candidates may remain `preview_only` while they are producer drafts.
Removing `preview_only` is an acceptance decision: it requires maintainer review
of the package subject, evidence, claims, version, selected relations, and any
legacy `xyflow.core` coexistence or supersession effect. Passing SpecHarvester
preflight, SpecPM handoff preflight, SpecPM AI enrichment preflight, or
`materialize-package-set` dry run is necessary review evidence, but it is not
approval to remove `preview_only`.

The broader lifecycle is documented in
`specs/CURATED_ACCEPTED_ARTIFACT_LIFECYCLE.md`: generated candidates are
immutable evidence, curated artifacts own maintainer-authored accepted
metadata, new harvests update curated artifacts only through review diffs,
evidence chains are preserved through `foreignArtifacts`, `preview_only`
removal is a maintainer acceptance act, and relation acceptance remains
separate from package acceptance.

A later fresh `xyflow` producer run can be recorded as
`SpecPMGeneratedCandidateRefreshDecision` with `updateNeeded: false` and
`reason: no_contract_delta` when it uses the same source revision, reproduces
the same contract-bearing generated files, and does not improve the curated
accepted artifacts. In that case, producer receipt churn or a newly emitted
quality report is useful review evidence, not a reason to mutate
`public-index/generated/xyflow.*` or churn the accepted registry metadata.

The example refresh decision fixture for this no-op outcome lives at:

```text
tests/fixtures/refresh_decisions/xyflow-no-update.example.json
```
