# Package Set Registry Metadata Shape

Status: Implemented additive `/v0` metadata
Updated: 2026-06-09
Scope: public `/v0` metadata shape for package sets, accepted package
relations, and scoped search results

## Purpose

This document defines the public registry metadata shape for package sets.

The static public-index generator publishes these fields from maintainer-owned
accepted-source metadata. It does not infer relations from producer output.

## Compatibility Boundary

Existing `/v0` consumers must remain able to read ordinary package metadata,
version metadata, capability search, and exact `intent.*` search without knowing
about package sets.

Package-set metadata is introduced through additive fields and extension-safe
defaults:

- missing package-set fields mean "ordinary package metadata";
- unknown relation fields must not grant authority;
- consumers may ignore relation context and still receive direct search results;
- package-set metadata must not merge member package records into aggregate
  package records.

## Package Metadata Additions

A package metadata record may expose:

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
        "version": "0.1.0",
        "type": "contains",
        "relation_id": "xyflow.workspace.contains.xyflow.system"
      },
      {
        "package_id": "xyflow.react",
        "version": "0.1.0",
        "type": "contains",
        "relation_id": "xyflow.workspace.contains.xyflow.react"
      },
      {
        "package_id": "xyflow.svelte",
        "version": "0.1.0",
        "type": "contains",
        "relation_id": "xyflow.workspace.contains.xyflow.svelte"
      }
    ]
  }
}
```

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
- `packageSet.members[].version`: member package version scoped by the accepted
  relation.
- `packageSet.members[].type`: relation type from the accepted relation
  vocabulary that connects the package set to the member.
- `packageSet.members[].relation_id`: accepted relation identifier.

Member summaries should not replace package lookup. Consumers that need member
metadata should query the member package directly.

## Relation Metadata

The public index also publishes accepted relations at:

```text
GET /v0/relations
```

The payload kind is `RemotePackageRelations`.

Package metadata may expose the same accepted relation summaries as
`relationContext[]`:

```json
{
  "relations": [
    {
      "id": "xyflow.workspace.contains.xyflow.react",
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

Relation metadata is accepted only from `public-index/accepted-packages.yml`
`relations[]` entries. Producer statuses such as `producer_observed` are not
accepted registry metadata.

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

The registry status payload advertises package-set support:

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

The static viewer renders:

- package-set badge for aggregate entrypoints;
- member list as links to exact package lookup;
- relation badges with short explanations;
- result scope in exact search results;
- direct matches separately from relation-context-only entries.

The viewer should not hide scoped packages under the aggregate package. Search
results should remain flat and scannable.

## Validation and Conformance

Regression tests cover:

- ordinary package payloads without package-set fields;
- package-set metadata with members;
- relation metadata with evidence;
- exact intent search with aggregate and package result scopes;
- consumers ignoring package-set fields while still reading direct results.

## Non-Goals

This metadata shape does not add:

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
