# Xyflow Package Set Reference Scenario

Status: Draft
Updated: 2026-06-06
Scope: reference scenario for package sets, monorepo discovery, and scoped
package candidates

## Purpose

This reference scenario shows how a multi-package repository can preserve broad
product discovery intent without overclaiming one scoped package.

It is a non-normative reference. It does not publish `xyflow` packages, change
the public registry, or accept generated packages automatically.

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

## Proposed Package Subjects

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

## Proposed Relations

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

The accepted-source materialization adds:

- `public-index/generated/xyflow.workspace/0.1.0`;
- `public-index/generated/xyflow.react/0.1.0`;
- `public-index/generated/xyflow.svelte/0.1.0`;
- `public-index/generated/xyflow.system/0.1.0`.

The generated package-set manifests intentionally keep `preview_only: true`.
This means they are visible accepted-source preview candidates, not final
non-preview claims. Removing `preview_only` remains a later maintainer decision
over package subject, evidence, claims, version, selected relations, and
`xyflow.core` coexistence or supersession effect.

Stable `/v0` relation metadata remains out of scope for this materialization
PR. The three selected `contains` relation IDs are carried in materialization
review evidence and PR notes until the drafted package-set relation metadata
shape is implemented.

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
