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

Maintainers may accept:

- only `xyflow.workspace`;
- one or more scoped member packages;
- selected `contains` relations;
- none of the generated candidates.

Accepting the package set does not accept all members. Accepting a member does
not accept the package set. Accepting a relation does not grant trust or
selection authority.
