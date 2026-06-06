# Package Set Registry Metadata Shape

Status: Draft
Updated: 2026-06-06
Scope: future public `/v0` metadata shape for package sets, package relations,
and scoped search results

## Purpose

This document defines the draft public registry metadata shape for package sets.

It is a design contract for future `/v0` evolution. It does not change the
current generator, static registry payloads, viewer, or client commands.

## Compatibility Boundary

Existing `/v0` consumers must remain able to read ordinary package metadata,
version metadata, capability search, and exact `intent.*` search without knowing
about package sets.

Package-set metadata should be introduced through additive fields and
extension-safe defaults:

- missing package-set fields mean "ordinary package metadata";
- unknown relation fields must not grant authority;
- consumers may ignore relation context and still receive direct search results;
- package-set metadata must not merge member package records into aggregate
  package records.

## Package Metadata Additions

A package metadata record may eventually expose:

```json
{
  "package_id": "xyflow.workspace",
  "version": "0.1.0",
  "subject": {
    "kind": "package_set",
    "scope": "aggregate"
  },
  "packageSet": {
    "profile": "specpm.package_set/v0",
    "setType": "workspace",
    "summary": "xyflow workspace for node-based editors and interactive flow systems.",
    "members": [
      {
        "package_id": "xyflow.system",
        "role": "core_runtime",
        "type": "contains"
      },
      {
        "package_id": "xyflow.react",
        "role": "react_binding",
        "type": "contains"
      },
      {
        "package_id": "xyflow.svelte",
        "role": "svelte_binding",
        "type": "contains"
      }
    ]
  }
}
```

Draft fields:

- `subject.kind`: `package` or `package_set`.
- `subject.scope`: display scope such as `package`, `aggregate`, or
  `abstract_contract`.
- `packageSet.profile`: package-set metadata profile identifier.
- `packageSet.setType`: repository, workspace, ecosystem, product_family,
  curated_family, migration_family, or another accepted vocabulary value.
- `packageSet.members[]`: member package summaries, not embedded package
  metadata.
- `packageSet.members[].package_id`: existing `/v0` package identifier field
  for the member package.
- `packageSet.members[].type`: relation type from the accepted relation
  vocabulary that connects the package set to the member.

Member summaries should not replace package lookup. Consumers that need member
metadata should query the member package directly.

## Relation Metadata

Package metadata may expose accepted relation summaries:

```json
{
  "relations": [
    {
      "type": "contains",
      "source": "xyflow.workspace",
      "target": "xyflow.react",
      "versionScope": {
        "sourceVersion": "0.1.0",
        "targetVersion": "0.1.0"
      },
      "evidence": [
        {
          "kind": "source_file",
          "path": "pnpm-workspace.yaml"
        }
      ],
      "reviewStatus": "accepted"
    }
  ]
}
```

Relation metadata must remain explicit. It must not imply:

- inherited capabilities;
- inherited constraints;
- inherited lifecycle state;
- inherited namespace ownership;
- trust propagation;
- automatic package selection.

## Search Result Additions

Exact capability and intent search results may expose direct match scope:

```json
{
  "package_id": "xyflow.react",
  "version": "0.1.0",
  "scope": "package",
  "match": "direct",
  "relationContext": [
    {
      "type": "contains",
      "source": "xyflow.workspace",
      "target": "xyflow.react"
    }
  ]
}
```

Draft fields:

- `scope`: `package`, `aggregate`, `abstract_contract`, or `related`.
- `match`: `direct` or `relation_context`.
- `relationContext[]`: optional accepted relation summaries that explain the
  result after discovery.

Direct matches should remain visible even when relation context is ignored.

## Intent Catalog Additions

Observed intent catalog entries may eventually expose result-scope counts:

```json
{
  "intentId": "intent.ui.node_based_editor",
  "observedPackages": 3,
  "observedScopes": {
    "aggregate": 1,
    "package": 2
  }
}
```

These counts are discovery metadata. They are not canonical taxonomy decisions.

## Status Payload Additions

The registry status payload may eventually advertise package-set support:

```json
{
  "supportedFeatures": [
    "package_sets",
    "package_relations",
    "search_result_scope"
  ]
}
```

Consumers should treat missing feature flags as absence of package-set metadata,
not registry failure.

## Viewer Expectations

A static viewer should render:

- package-set badge for aggregate entrypoints;
- member list as links to exact package lookup;
- relation badges with short explanations;
- result scope in exact search results;
- direct matches separately from relation-context-only entries.

The viewer should not hide scoped packages under the aggregate package. Search
results should remain flat and scannable.

## Validation and Conformance

Future conformance fixtures should cover:

- ordinary package payloads without package-set fields;
- package-set metadata with members;
- relation metadata with evidence;
- exact intent search with aggregate and package result scopes;
- consumers ignoring package-set fields while still reading direct results.

## Non-Goals

This metadata shape does not add:

- runtime generator implementation;
- registry mutation APIs;
- package-set acceptance automation;
- relation inference;
- relation path expansion as default search;
- dependency solving;
- semantic search;
- package execution;
- trust propagation.

## Future Work

Follow-up tasks should implement or document:

- generator output changes;
- viewer rendering;
- conformance fixtures;
- multi-package producer bundle intake;
- `xyflow` reference payloads.

SpecHarvester package-set producer output expectations are defined in
`specs/SPECHARVESTER_MONOREPO_DISCOVERY.md`.
