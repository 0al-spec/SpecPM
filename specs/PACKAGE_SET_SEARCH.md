# Package Set Index and Search Semantics

Status: Draft
Updated: 2026-06-06
Scope: exact index and search behavior for package sets and scoped package
results

## Purpose

This document defines how package sets should participate in exact package,
capability, and `intent.*` lookup.

The central rule is:

```text
discovery is index-based, not tree-traversal-based
```

A consumer should not need to know whether the useful result lives at a
repository entrypoint, a scoped package, an abstract contract, or a related
package before running exact lookup.

## Search Model

SpecPM exact search should index what a package explicitly declares. Package
sets may declare aggregate discovery metadata. Member packages may declare
scoped capabilities and intents. Relations may explain how results are connected
after discovery.

The search path is:

```text
exact query -> direct indexed matches -> optional relation context
```

not:

```text
exact query -> root package -> traverse members -> infer leaf meaning
```

and not:

```text
exact query -> member package -> inherit aggregate package intents
```

## Result Scope

Search results that may include package sets should expose an explicit result
scope. The initial vocabulary is:

- `package`: a concrete or scoped `SpecPackage` result;
- `aggregate`: a package-set or collection entrypoint result;
- `abstract_contract`: an abstract intent-level or interface contract result;
- `related`: a result surfaced only as relation context, not as a direct match.

The result scope is descriptive metadata. It does not change package validity,
lifecycle state, trust, or selection authority.

## Direct Matches

A direct match exists when the indexed package record explicitly declares the
searched value.

Examples:

- a scoped package declares a capability ID in `index.provides.capabilities`;
- a scoped package declares an `intent.*` mapping through capability
  `intentIds`;
- a package set declares aggregate `index.provides.intents`;
- an abstract package declares an intent-level contract capability.

Direct matches may appear in exact search results.

## Relation Context

Relation context explains connections around direct matches. It should not
create additional direct matches unless a future query mode explicitly asks for
relation expansion.

Example:

```json
{
  "intent": "intent.ui.node_based_editor",
  "results": [
    {
      "package": "xyflow.workspace",
      "version": "0.1.0",
      "scope": "aggregate",
      "match": "direct"
    },
    {
      "package": "xyflow.react",
      "version": "0.1.0",
      "scope": "package",
      "match": "direct",
      "relations": [
        {
          "type": "contains",
          "source": "xyflow.workspace",
          "target": "xyflow.react"
        }
      ]
    }
  ]
}
```

The `contains` relation helps users understand the result. It is not required to
discover `xyflow.react`.

## Capability Search

Exact capability search should continue to match package-owned capability IDs.

Package sets should avoid declaring member-owned capabilities as if they were
aggregate capabilities. A package set may declare an aggregate capability only
when the aggregate package-set subject itself owns that reviewable capability.

For example:

```text
xyflow.workspace.overview
```

could be an aggregate capability if the package set owns an overview/discovery
contract. It should not silently re-export:

```text
xyflow.react.node_editor
xyflow.svelte.node_editor
xyflow.system.flow_runtime
```

unless a future schema adds an explicit re-export model with evidence and
consumer-facing semantics.

## Intent Search

Exact `intent.*` lookup may return aggregate and scoped packages side by side
when both explicitly declare the intent.

Example:

```text
intent.ui.node_based_editor
```

may return:

```text
xyflow.workspace scope=aggregate match=direct
xyflow.react     scope=package   match=direct
xyflow.svelte    scope=package   match=direct
```

A narrower intent:

```text
intent.ui.flow_system_utilities
```

may return only:

```text
xyflow.system scope=package match=direct
```

The package set should not receive that narrower result unless it explicitly
declares the narrower intent as aggregate metadata.

## Package Lookup

Package lookup by exact package ID remains exact:

```text
xyflow.workspace
xyflow.system
xyflow.react
xyflow.svelte
```

Each package ID resolves to its own metadata, versions, lifecycle state,
receipts, accepted-source evidence, and relation context.

Package lookup may include relation summaries, but it must not merge member
metadata into the package-set record or merge package-set metadata into member
records.

## Ordering

Exact search ordering should be deterministic and should not imply authority.

Recommended ordering:

1. direct matches before relation-context-only matches;
2. non-yanked and non-deprecated versions before yanked or deprecated versions;
3. stable versions before pre-release versions when all other selection inputs
   are equal;
4. package ID lexical order as a final tie-breaker.

Consumers may group results by scope for display, but grouping must not change
the underlying match semantics.

## Ambiguity

Returning multiple direct matches is not an error. It is the expected result for
shared intents.

Selection belongs to the consumer, downstream resolver, SpecGraph, ContextBuilder,
or human reviewer. SpecPM should expose enough exact metadata for review without
choosing a package silently.

## Non-Goals

This search model does not add:

- semantic search;
- natural-language query interpretation;
- relation path expansion as default behavior;
- inherited member capabilities;
- inherited aggregate intents;
- automatic package selection;
- dependency solving;
- trust propagation;
- package execution.

## Future Work

Follow-up tasks should define:

- public `/v0` fields for result scope and relation context;
- viewer rendering for aggregate and scoped search results;
- conformance fixtures for package-set search payloads;
- optional explicit relation-expansion query modes, if needed;
- SpecHarvester output expectations for aggregate and scoped intent metadata.

